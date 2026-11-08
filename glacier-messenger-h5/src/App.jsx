import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Map, BookOpenText } from 'lucide-react'
import {
  CHAPTERS,
  ENDINGS,
  L0_VIDEOS,
} from './story/story.js'
import {
  freshGame,
  getChapter,
  commitChoice,
  conditionMet,
  computeScore,
} from './story/engine.js'
import { makeT, pick, gradeOf, DEFAULT_LANG, pickVO } from './i18n/ui.js'
import { useVideoPool } from './hooks/useVideoPool.js'
import { voSegments, useVoiceOver } from './hooks/useVoiceOver.js'
import {
  Ambience,
  SoundButton,
  LanguageSelector,
  TitleBlock,
  ChapterTitle,
} from './components/Chrome.jsx'
import StatusPanel from './components/StatusPanel.jsx'
import Narration from './components/Narration.jsx'
import ChoicePrompt, { ChoiceButton } from './components/ChoicePrompt.jsx'
import LiveTicker from './components/LiveTicker.jsx'
import { useStats } from './hooks/useStats.js'
import PooledVideo from './components/PooledVideo.jsx'
import { TransitionOverlay, WechatGuide, RegisterModal } from './components/Overlays.jsx'
import QteOverlay from './components/QteOverlay.jsx'
import EndingView from './components/EndingView.jsx'

/* ───────────────────────── 本地存储小工具 ───────────────────────── */
const LS = {
  get(key, fallback) {
    try {
      const v = localStorage.getItem(key)
      return v == null ? fallback : JSON.parse(v)
    } catch {
      return fallback
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {
      /* noop */
    }
  },
}
const isWechat = () => /MicroMessenger/i.test(navigator.userAgent || '')

/**
 * 复制链接：必须给调用方返回「到底成没成」。
 * 微信 X5 / 老内核里 navigator.clipboard 常存在但 writeText 会被权限拒绝，
 * 若静默吞掉，UI 会显示「已复制」而剪贴板其实是空的 —— 玩家以为复制成功了。
 */
async function copyText(text) {
  const legacy = () => {
    try {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.setAttribute('readonly', '')
      ta.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;opacity:0'
      document.body.appendChild(ta)
      ta.select()
      ta.setSelectionRange(0, text.length)
      const ok = document.execCommand('copy')
      document.body.removeChild(ta)
      return ok
    } catch {
      return false
    }
  }
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
    /* 落到下面的兜底 */
  }
  return legacy()
}

/* ───────────────────────── 应用根组件 ───────────────────────── */
export default function App() {
  const [lang, setLang] = useState(() => LS.get('gm_lang', DEFAULT_LANG))
  // 首屏为让视频能自动起播，初始一律静音；
  // 玩家点「开始游戏」那一刻（真实用户手势）再自动开声，见 onRegister。
  const [muted, setMuted] = useState(() => LS.get('gm_muted', true))
  const autoUnmuteRef = useRef(() => LS.get('gm_muted', null) === null)
  const [game, setGame] = useState(() => freshGame())
  const [transition, setTransition] = useState(null) // {kind, videoName, text, result}
  const [qteChoice, setQteChoice] = useState(null)
  const [showWechat, setShowWechat] = useState(() => isWechat() && !LS.get('gm_wechat_ok', false))
  const [showRegister, setShowRegister] = useState(() => !LS.get('gm_identity', null))
  const [unlocked, setUnlocked] = useState(() => LS.get('gm_endings', []))
  const [showNetTip, setShowNetTip] = useState(false)
  const [voOn, setVoOn] = useState(() => LS.get('gm_vo', true))
  /* 章节正片是否已完整播过一遍（loop 模式下靠 timeupdate 逼近片尾判定） */
  const [videoDone, setVideoDone] = useState(false)
  /* 「看完还没选」的催选弹窗；每章最多弹一次，玩家关掉后不再打扰 */
  const [showChoicePrompt, setShowChoicePrompt] = useState(false)
  const promptedRef = useRef(new Set())

  const t = useMemo(() => makeT(lang), [lang])
  const vo = useMemo(() => pickVO(lang), [lang])

  /* 访问统计：游客同样计入；后端不可达时静默降级 */
  const { live: liveStats } = useStats({
    lang,
    chapterId: game.chapterId,
    endingKey: game.ending,
  })
  const pool = useVideoPool({ maxLive: 4 })
  const busyRef = useRef(false)
  const chapter = getChapter(game.chapterId)
  const endingData = game.ending ? ENDINGS[game.ending] : null
  const score = computeScore(game.stats)
  const grade = gradeOf(score, lang)

  /* 剧情旁白：按 VO 编号逐句播放 + 字幕高亮。
     ids 引用必须 memo 化，否则每次渲染都会新建数组 → 触发重播。 */
  const descSegs = useMemo(() => (chapter ? voSegments(`chapter:${chapter.id}:desc`) : []), [chapter?.id]) // eslint-disable-line react-hooks/exhaustive-deps
  const descIds = useMemo(() => descSegs.map((s) => s.id), [descSegs])
  /* 过场浮层 / QTE 弹出时必须停掉本章旁白：
     这两个阶段 chapterId 还没变，若不停，旧章节的配音会一路念到新章节里去。 */
  const { activeId: voActiveId, finished: voFinished, blocked: voBlocked, resume: resumeVo } = useVoiceOver({
    ids: descIds,
    lang,
    enabled: voOn && !!chapter && !endingData && !showRegister && !transition && !qteChoice,
  })

  /* 语言切换持久化 + <html lang> + 标签页标题（index.html 里的静态标题是英文兜底） */
  useEffect(() => {
    LS.set('gm_lang', lang)
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : lang
    document.title = t('title')
  }, [lang, t])
  useEffect(() => LS.set('gm_muted', muted), [muted])

  /* 浏览器拦截了有声播放（无手势）→ 把开关拨回静音，别让 UI 和实际不一致 */
  const onMediaBlocked = useCallback(() => setMuted(true), [])

  /* 任意浮层打开时锁背景滚动：iOS Safari 有「滚动穿透」，
     弹窗里滑动会带着后面的页面一起动（输入框聚焦时尤其明显）。 */
  const overlayOpen = !!(showWechat || showRegister || transition || qteChoice || showChoicePrompt)
  useEffect(() => {
    if (!overlayOpen) return undefined
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [overlayOpen])

  /* 声音开关：必须在点击回调里同步作用到池内元素，
     这样「解除静音」发生在真实手势上下文中，浏览器才会放行。 */
  const toggleSound = useCallback(() => {
    setMuted((m) => {
      const next = !m
      pool.applyMuted?.(next)
      return next
    })
  }, [pool])
  useEffect(() => LS.set('gm_vo', voOn), [voOn])

  /* 首屏带宽全部让给章节正片；正片下完后，预取交给下面的「按章按需预取」接管 */
  useEffect(() => {
    if (pool.netSlow) setShowNetTip(true)
    // 章节正片（L0）由 PooledVideo 直接播放，此处只等它彻底下完，
    // 期间不放行任何预取 —— 保证首屏起播不被抢带宽。
    pool.whenBuffered(L0_VIDEOS[0], 25000).then(() => pool.releaseGate())
  }, [pool])

  /* 慢网提示只弹一次 */
  useEffect(() => {
    if (!showNetTip) return
    const id = setTimeout(() => setShowNetTip(false), 6000)
    return () => clearTimeout(id)
  }, [showNetTip])

  /* 微信引导关闭后不再弹 */
  const closeWechat = useCallback(() => {
    LS.set('gm_wechat_ok', true)
    setShowWechat(false)
  }, [])

  /* copied: null=未操作 / true=成功 / false=失败（老内核要提示玩家手动复制） */
  const [copied, setCopied] = useState(null)
  const copyLink = useCallback(() => {
    copyText(window.location.href).then(setCopied)
  }, [])

  /* 进入新章节：分支感知预取 + 裁剪预取窗口外的元素 */
  useEffect(() => {
    if (!chapter) return
    const next = CHAPTERS.find((c) => c.id === chapter.id + 1)
    const keep = [
      chapter.video,
      ...chapter.choices.map((c) => c.animation).filter(Boolean),
      ...(next ? [next.video, ...next.choices.map((c) => c.animation).filter(Boolean)] : []),
    ].filter(Boolean)
    // 分支感知预取走串行队列；只取「本章两个后果片 + 下一章正片」，
    // 不下下一章的分支片（等真正进入那一章再取），把预取流量压到最小。
    // 慢网/省流模式下进一步只保「本章后果片」——玩家即将点击所必需的那两个。
    const next2 = CHAPTERS.find((c) => c.id === chapter.id + 1)
    const upcoming = [
      ...chapter.choices.map((c) => c.animation).filter(Boolean),
      ...(next2 && !pool.netSlow ? [next2.video] : []),
    ].filter(Boolean)
    pool.enqueue(upcoming)
    pool.prune(keep)
    window.scrollTo({ top: 0, behavior: 'auto' })
  }, [game.chapterId]) // eslint-disable-line react-hooks/exhaustive-deps

  /* 换章：重置「正片是否播完」、收起催选弹窗；
     并挂一个 45s 兜底 —— 视频卡住或被浏览器拦住时，也不能把催选弹窗永远锁死。 */
  useEffect(() => {
    setVideoDone(false)
    setShowChoicePrompt(false)
    const id = setTimeout(() => setVideoDone(true), 45000)
    return () => clearTimeout(id)
  }, [game.chapterId])

  /* 旁白念完 + 正片播过一遍，玩家还没点选项 → 弹窗把选项递到手边。
     每章只弹一次：关掉（或选了）之后不再打扰。 */
  const voDone = !voOn || !descIds.length || voFinished || voBlocked
  useEffect(() => {
    if (!chapter || endingData || showRegister) return
    if (transition || qteChoice) return
    if (!voDone || !videoDone) return
    if (promptedRef.current.has(chapter.id)) return
    const id = setTimeout(() => {
      promptedRef.current.add(chapter.id)
      setShowChoicePrompt(true)
    }, 700)
    return () => clearTimeout(id)
  }, [chapter?.id, voDone, videoDone, transition, qteChoice, showRegister, endingData]) // eslint-disable-line react-hooks/exhaustive-deps

  /* 浮层盖住页面时暂停章节正片：省下解码开销给后果片，手机上差别明显 */
  useEffect(() => {
    const v = chapter?.video
    if (!v) return
    if (transition || qteChoice || showRegister) pool.pause?.(v)
    else pool.resume?.(v)
  }, [transition, qteChoice, showRegister, game.chapterId, pool]) // eslint-disable-line react-hooks/exhaustive-deps

  /* 结局：只保留结局正片，其余全释放 */
  useEffect(() => {
    if (game.ending) pool.prune([ENDINGS[game.ending].video])
  }, [game.ending]) // eslint-disable-line react-hooks/exhaustive-deps

  /* ───────────────────── 选择与流转 ───────────────────── */
  const beginTransition = useCallback(
    (choice, result, consText) => {
      busyRef.current = true
      // 先把数值/状态位立刻落到 UI（对标参考站：点击即 effects 生效）
      setGame((g) => ({
        ...g,
        stats: result.stats,
        state: result.state,
        history: [...g.history, choice.id],
      }))
      setTransition({
        kind: choice.animation ? 'animation' : 'loading',
        videoName: choice.animation || null,
        text: consText,
        result,
      })
    },
    [],
  )

  const onChoose = useCallback(
    (choice) => {
      if (busyRef.current || transition || qteChoice) return
      if (!conditionMet(choice, game.state, game.stats)) return
      // 做了选择就收起催选弹窗（不管从页面还是弹窗里点的）
      setShowChoicePrompt(false)

      if (choice.qte) {
        // QTE 有时限，趁倒计时先把后果片段拉下来
        if (choice.animation) pool.prefer?.([choice.animation])
        setQteChoice(choice)
        return
      }
      // 后果动画马上就要播，提前插队预取（不等正片让路），否则浮层里会干等转圈
      if (choice.animation) pool.prefer?.([choice.animation])
      const result = commitChoice(game, choice)
      // 若这一步直接进结局：趁转场浮层还在放，先把结局正片拉下来。
      // 否则转场结束、结局页挂载时才开始下载，玩家看到的就是一段黑屏转圈。
      if (result.ending && ENDINGS[result.ending]) pool.prefer?.([ENDINGS[result.ending].video])
      beginTransition(choice, result, pick(choice.consequences, lang))
    },
      [game, lang, transition, qteChoice, beginTransition, pool],
  )

  const onQteFinish = useCallback(
    (success) => {
      const choice = qteChoice
      if (!choice) return
      setQteChoice(null)
      if (choice.animation) pool.prefer?.([choice.animation])
      const effects = success
        ? choice.effects
        : { ...choice.effects, health: Math.max(0, (choice.effects?.health ?? 0) - 15) }
      const base = pick(choice.consequences, lang)
      const consText = success
        ? `${t('qteSuccess')}\n${base}`
        : `${t('qteFail')}\n${base}`
      const result = commitChoice(game, { ...choice, effects })
      if (result.ending && ENDINGS[result.ending]) pool.prefer?.([ENDINGS[result.ending].video])
      beginTransition(choice, result, consText)
    },
    [qteChoice, game, lang, t, beginTransition, pool],
  )

  const onTransitionDone = useCallback(() => {
    const cur = transition
    if (!cur) return
    busyRef.current = false
    setTransition(null)
    const { result } = cur
    if (result.ending) {
      setGame((g) => ({ ...g, ending: result.ending }))
      setUnlocked((prev) => {
        const next = prev.includes(result.ending) ? prev : [...prev, result.ending]
        LS.set('gm_endings', next)
        return next
      })
      // 结局不再弹窗打断，玩家身份已在开局登记
    } else if (result.nextChapterId) {
      setGame((g) => ({ ...g, chapterId: result.nextChapterId }))
    }
  }, [transition])

  const onRestart = useCallback(() => {
    busyRef.current = false
    setTransition(null)
    setQteChoice(null)
    setShowRegister(false)
    setShowChoicePrompt(false)
    promptedRef.current.clear() // 重开一局，催选弹窗重新计
    setGame(freshGame())
    pool.prune([L0_VIDEOS[0]])
  }, [pool])

  /* 开局登记：匿名或具名都视为已登记，之后不再弹（对标参考站 playerData 判定） */
  const onRegister = useCallback((payload) => {
    LS.set('gm_identity', {
      name: payload.isAnonymous ? '' : payload.name.trim(),
      email: payload.email || '',
      isAnonymous: !!payload.isAnonymous,
      at: new Date().toISOString(),
    })
    setShowRegister(false)
    /* 这是一次真实用户手势 —— 趁此解除静音，玩家才听得到后果片的声音。
       只自动做一次（此前没存过偏好时），之后完全尊重玩家自己的选择。 */
    if (autoUnmuteRef.current) {
      autoUnmuteRef.current = false
      pool.applyMuted?.(false)
      setMuted(false)
    }
  }, [pool])

  /* ───────────────────── 渲染 ───────────────────── */
  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-gradient-to-b from-slate-900 via-blue-900 to-slate-800 text-white">
      {/* 开局登记弹窗期间隐藏悬浮控件，避免与弹窗右上角语言选择器重叠 */}
      {!showRegister && (
        <SoundButton muted={muted} onToggle={toggleSound} label={muted ? t('soundOn') : t('soundOff')} />
      )}

      {showWechat && <WechatGuide t={t} onClose={closeWechat} onCopy={copyLink} copied={copied} />}

      {transition && (
        <TransitionOverlay
          pool={pool}
          kind={transition.kind}
          videoName={transition.videoName}
          text={transition.text}
          muted={muted}
          lang={lang}
          onBlocked={onMediaBlocked}
          onDone={onTransitionDone}
        />
      )}

      {qteChoice && <QteOverlay t={t} choice={qteChoice} onFinish={onQteFinish} />}

      {showChoicePrompt && chapter && !endingData && (
        <ChoicePrompt
          t={t}
          lang={lang}
          choices={chapter.choices}
          game={game}
          conditionMet={conditionMet}
          onChoose={onChoose}
          onDismiss={() => setShowChoicePrompt(false)}
        />
      )}

      {showRegister && (
        <RegisterModal t={t} lang={lang} onLangChange={setLang} onSubmit={onRegister} />
      )}

      {showNetTip && (
        <div className="fixed bottom-4 left-1/2 z-[70] w-[min(92vw,26rem)] -translate-x-1/2 rounded-lg border border-amber-400/30 bg-amber-500/15 px-4 py-3 text-sm text-amber-100 backdrop-blur-sm animate-fade-up">
          <span className="font-semibold">{t('netSlowTitle')}：</span>
          {t('netSlowBody')}
        </div>
      )}

      <Ambience />

      <div className="relative z-10 mx-auto max-w-4xl px-4 pb-8 pt-4 safe-x">
        {/* 顶栏：左上标题 · 右上语言选择 + 雁群状态（右侧留 48px 给悬浮声音按钮） */}
        {/* 左右留白由外层 .safe-x 提供（已修好为 max(1rem, 安全区)），此处只给右上角悬浮按钮让位 */}
        <header className="mb-3 flex items-start justify-between gap-3 pr-[72px]">
          <TitleBlock t={t} />
          <div className="flex shrink-0 flex-col items-end gap-1.5">
            <LanguageSelector lang={lang} onChange={setLang} inline />
            <StatusPanel t={t} stats={game.stats} compact />
          </div>
        </header>

        {liveStats && (
          <div className="mb-4">
            <LiveTicker live={liveStats} t={t} />
          </div>
        )}

        {endingData ? (
          <EndingView
            pool={pool}
            t={t}
            lang={lang}
            ending={endingData}
            endingKey={game.ending}
            voOn={voOn}
            muted={muted}
            onBlocked={onMediaBlocked}
            stats={game.stats}
            score={score}
            grade={grade}
            onRestart={onRestart}
          />
        ) : (
          chapter && (
            <div
              className="mx-auto flex w-full max-w-[1920px] flex-col px-0 space-y-6"
              style={{ minHeight: 'var(--vh60, 60vh)' }}
            >
              {/* 章节标题 */}
              <div className="w-full text-center">
                <ChapterTitle icon={Map} label={`${t('chapterPrefix', { n: chapter.id })} · ${pick(chapter.title, lang)}`} />
              </div>

              {/* 章节正片（上）+ 剧情旁白（下） */}
              <div className="w-full rounded-lg border border-cyan-500/30 bg-gradient-to-r from-blue-900/40 to-purple-900/40 p-4 backdrop-blur-sm sm:p-6">
                {chapter.video && (
                  <div className="mb-4 rounded border border-cyan-400">
                    <PooledVideo
                      pool={pool}
                      name={chapter.video}
                      muted={muted}
                      /* 旁白念台词时把画面音压下去，避免两路声音打架 */
                      volume={voActiveId ? 0.22 : 0.7}
                      onBlocked={onMediaBlocked}
                      onCompleted={() => setVideoDone(true)}
                      shellClass="w-full"
                      lang={lang}
                      eager
                    />
                  </div>
                )}
                <div className="flex items-start gap-3 sm:gap-4">
                  <BookOpenText className="h-7 w-7 shrink-0 text-cyan-400 sm:h-8 sm:w-8" />
                  <div className="min-w-0 flex-1">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <span className="text-[11px] uppercase tracking-[0.2em] text-cyan-400/80">
                        {vo.label}
                        {voActiveId ? ` · ${vo.playing}` : ''}
                      </span>
                      <button
                        type="button"
                        data-vo-toggle
                        onClick={() => setVoOn((v) => !v)}
                        className="shrink-0 rounded border border-cyan-400/40 px-2 py-0.5 text-[11px] text-cyan-200 hover:bg-cyan-400/10"
                      >
                        {voOn ? vo.on : vo.off}
                      </button>
                    </div>
                    {/* 旁白：默认只显示当前这一句，点「展开全文」铺开整段 */}
                    <Narration
                      segs={descSegs}
                      fallback={pick(chapter.description, lang)}
                      activeId={voActiveId}
                      lang={lang}
                      t={t}
                      blocked={voBlocked}
                      onResume={resumeVo}
                      blockedLabel={vo.blocked}
                    />
                  </div>
                </div>
              </div>

              {/* 选项 */}
              <div className="w-full space-y-4">
                <h3 className="text-center text-xl font-semibold text-cyan-300">{t('choicePrompt')}</h3>
                {chapter.choices.map((choice) => (
                  <ChoiceButton
                    key={choice.id}
                    choice={choice}
                    locked={!conditionMet(choice, game.state, game.stats)}
                    lang={lang}
                    t={t}
                    onChoose={onChoose}
                  />
                ))}

                {unlocked.length > 0 && (
                  <p className="pt-2 text-center text-xs text-gray-500">
                    {t('endingProgress')} · {t('endingsOf', { n: Object.keys(ENDINGS).length })} ·{' '}
                    {unlocked.length}/{Object.keys(ENDINGS).length}
                  </p>
                )}
              </div>
            </div>
          )
        )}
      </div>
    </div>
  )
}
