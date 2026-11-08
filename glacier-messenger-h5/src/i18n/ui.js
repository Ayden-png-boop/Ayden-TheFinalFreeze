/**
 * 四语 UI 文案表。
 * 键名与参考站一致（title / subtitle / flockStatus / cooperation / radical / health ...），
 * 便于逐项对标复刻。
 */

export const LANGS = [
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
]

export const DEFAULT_LANG = 'en'

export const UI = {
  zh: {
    title: '冰川信使：斑头雁的2040',
    subtitle: '一个关于气候变化的互动故事',
    flockStatus: '雁群状态',
    cooperation: '合作值',
    radical: '激进值',
    health: '体力值',
    chapterPrefix: '第{n}章',
    choicePrompt: '请做出你的抉择',
    narrationExpand: '展开全文',
    narrationCollapse: '收起',
    sentOf: '第 {i}/{n} 句',
    choiceNowBody: '旁白与影像都已看完，请选择下一步。',
    choiceLater: '再想想',
    conditionNotMet: '条件未满足 — 缺少必要的前置条件',
    effectUnlock: '解锁',
    finalStats: '最终数值',
    cooperationStat: '合作值',
    radicalStat: '激进值',
    healthStat: '体力值',
    totalScore: '综合得分',
    scoreGrade: '你的身份',
    restart: '重新开始',
    loadingScene: '正在加载场面…',
    chooseScene: '正在模拟后果…',
    langLabel: '语言',
    soundOn: '播放声音',
    soundOff: '静音',

    // 在线播报（游客一并计入）
    livePlaying: '{n} 人正在游玩',
    livePlayed: '{n} 人玩过本作',

    // 微信内打开引导
    wechatTitle: '提示',
    wechatBody:
      '检测到您正在微信中浏览，为了获得更好的视频播放体验，建议在默认浏览器中打开。',
    copyLink: '复制链接',
    copied: '链接已复制',
    copyFail: '复制失败，请长按地址栏手动复制',
    copyFailHint: '当前浏览器不支持一键复制，请长按页面顶部地址栏复制链接。',
    tapToPlay: '轻触播放',
    usageTitle: '使用方法：',
    usage1: '1. 点击右上角"..."菜单',
    usage2: '2. 选择"用默认浏览器打开"',
    orLabel: '或：',
    usage3: '1. 点击"复制链接"',
    usage4: '2. 粘贴连接到浏览器并访问',
    stayInWechat: '继续在微信中使用',

    // 开局参与方式弹窗（对标参考站 intro 阶段弹窗）
    welcomeTitle: '欢迎来到冰川信使',
    welcomeSubtitle: '开始游戏前，请选择您的参与方式',
    anonymous: '匿名参与',
    nameLabel: '姓名',
    namePlaceholder: '请输入姓名',
    emailLabel: '邮箱',
    emailOptional: '(可选)',
    emailPlaceholder: '请输入邮箱（可选）',
    emailInvalid: '请输入有效的邮箱地址',
    startGame: '开始游戏',
    startAnonymous: '匿名开始游戏',
    registering: '正在注册…',
    entering: '正在进入…',
    privacy:
      '🔒 我们重视您的隐私。您的个人信息仅用于游戏体验改进，不会被用于其他用途。您可以选择匿名参与，或随时删除您的数据。',

    // QTE
    qteTitle: 'QTE · 夜袭采矿站',
    qteBrief: '30 秒内关闭 {n} 处矿井阀门',
    qteTime: '剩余时间',
    qteProgress: '已关闭',
    qteHint: '快速点击浮现的阀门，关满即成功',
    qteGo: '开始突袭',
    qteSuccess: '突袭成功！连破 2 座矿井',
    qteFail: '突袭失败！巡逻犬咬伤雁群',
    qteAgain: '重新尝试',

    // 结局
    endingTag: '结局',
    endingProgress: '你的迁徙已完成',
    endingsOf: '共 {n} 种结局',
    revisit: '你已做出全部抉择',

    // 网络/视频状态
    netSlowTitle: '网络较慢',
    netSlowBody: '已自动切换到省流模式，画质略有降低以保证流畅播放。',
    netSlowOk: '知道了',
    videoFallback: '视频加载中…',
  },

  en: {
    title: 'Glacier Messenger: Bar-headed Goose 2040',
    subtitle: 'An interactive story about climate change',
    flockStatus: 'Flock Status',
    cooperation: 'Cooperation',
    radical: 'Radical',
    health: 'Stamina',
    chapterPrefix: 'Chapter {n}',
    choicePrompt: 'Make Your Choice',
    narrationExpand: 'Show full text',
    narrationCollapse: 'Collapse',
    sentOf: '{i}/{n}',
    choiceNowBody: "You've reached the end of the scene — choose your next step.",
    choiceLater: 'Not yet',
    conditionNotMet: 'Locked — required conditions not met',
    effectUnlock: 'Unlock',
    finalStats: 'Final Stats',
    cooperationStat: 'Cooperation',
    radicalStat: 'Radical',
    healthStat: 'Stamina',
    totalScore: 'Total Score',
    scoreGrade: 'Your Role',
    restart: 'Restart',
    loadingScene: 'Loading scene…',
    chooseScene: 'Simulating consequences…',
    langLabel: 'Language',
    soundOn: 'Unmute',
    soundOff: 'Mute',

    // Live ticker (visitors included)
    livePlaying: '{n} playing now',
    livePlayed: '{n} have played',

    wechatTitle: 'Notice',
    wechatBody:
      'You appear to be browsing inside WeChat. For a better video experience, please open this page in your default browser.',
    copyLink: 'Copy Link',
    copied: 'Link copied',
    copyFail: 'Copy failed — long-press the address bar',
    copyFailHint: 'This browser blocks clipboard access. Long-press the address bar to copy.',
    tapToPlay: 'Tap to play',
    usageTitle: 'How to open:',
    usage1: '1. Tap the "..." menu at the top right',
    usage2: '2. Choose "Open in browser"',
    orLabel: 'Or:',
    usage3: '1. Tap "Copy Link"',
    usage4: '2. Paste the link into your browser',
    stayInWechat: 'Continue in WeChat',

    welcomeTitle: 'Welcome to Glacier Messenger',
    welcomeSubtitle: 'Before starting, please choose your participation mode',
    anonymous: 'Anonymous',
    nameLabel: 'Name',
    namePlaceholder: 'Please enter your name',
    emailLabel: 'Email',
    emailOptional: '(optional)',
    emailPlaceholder: 'Please enter your email (optional)',
    emailInvalid: 'Please enter a valid email address',
    startGame: 'Start Game',
    startAnonymous: 'Start Anonymously',
    registering: 'Registering…',
    entering: 'Entering…',
    privacy:
      '🔒 We value your privacy. Your personal info is only used to improve the game experience and will not be used for other purposes. You can choose to play anonymously or delete your data at any time.',

    qteTitle: 'QTE · Night Raid on the Mine',
    qteBrief: 'Close {n} mine valves within 30 seconds',
    qteTime: 'Time Left',
    qteProgress: 'Closed',
    qteHint: 'Tap the valves as they appear — close them all to succeed',
    qteGo: 'Begin the Raid',
    qteSuccess: 'Raid successful! Two mines disabled',
    qteFail: 'Raid failed! The flock was mauled by patrol dogs',
    qteAgain: 'Try Again',

    endingTag: 'Ending',
    endingProgress: 'Your migration is complete',
    endingsOf: '{n} endings in total',
    revisit: 'You have made every choice',

    netSlowTitle: 'Slow Network',
    netSlowBody:
      'Switched to data-saver mode automatically. Quality is slightly reduced to keep playback smooth.',
    netSlowOk: 'Got it',
    videoFallback: 'Loading video…',
  },

  ja: {
    title: '氷河の使者：インドガン2040',
    subtitle: '気候変動に関するインタラクティブストーリー',
    flockStatus: '群れの状態',
    cooperation: '協力値',
    radical: '過激値',
    health: '体力値',
    chapterPrefix: '第{n}章',
    choicePrompt: '選択してください',
    narrationExpand: '全文を表示',
    narrationCollapse: '折りたたむ',
    sentOf: '{i}/{n} 句',
    choiceNowBody: 'ナレーションと映像が終わりました。次を選んでください。',
    choiceLater: 'まだ選ばない',
    conditionNotMet: '条件未達成 — 前提条件を満たしていません',
    effectUnlock: '解放',
    finalStats: '最終数値',
    cooperationStat: '協力値',
    radicalStat: '過激値',
    healthStat: '体力値',
    totalScore: '総合スコア',
    scoreGrade: 'あなたの立場',
    restart: 'もう一度',
    loadingScene: 'シーンを読み込み中…',
    chooseScene: '結果をシミュレーション中…',
    langLabel: '言語',
    soundOn: '音を出す',
    soundOff: 'ミュート',

    // オンライン速報（ゲストも含む）
    livePlaying: '{n} 人がプレイ中',
    livePlayed: '{n} 人がプレイ済み',

    wechatTitle: 'お知らせ',
    wechatBody:
      'WeChat 内で閲覧しているようです。より良い動画再生のために、標準ブラウザで開くことをおすすめします。',
    copyLink: 'リンクをコピー',
    copied: 'コピーしました',
    copyFail: 'コピー失敗：アドレスバーを長押ししてください',
    copyFailHint: 'このブラウザはクリップボードに対応していません。アドレスバーを長押ししてコピーしてください。',
    tapToPlay: 'タップして再生',
    usageTitle: '開き方：',
    usage1: '1. 右上の「…」メニューをタップ',
    usage2: '2. 「ブラウザで開く」を選択',
    orLabel: 'または：',
    usage3: '1. 「リンクをコピー」をタップ',
    usage4: '2. ブラウザに貼り付けてアクセス',
    stayInWechat: 'WeChat のまま続ける',

    welcomeTitle: '氷河の使者へようこそ',
    welcomeSubtitle: 'ゲームを始める前に、参加方法をお選びください',
    anonymous: '匿名で参加する',
    nameLabel: 'お名前',
    namePlaceholder: 'お名前を入力してください',
    emailLabel: 'メールアドレス',
    emailOptional: '(任意)',
    emailPlaceholder: 'メールアドレスを入力（任意）',
    emailInvalid: '有効なメールアドレスを入力してください',
    startGame: 'ゲームを始める',
    startAnonymous: '匿名でゲームを始める',
    registering: '登録中…',
    entering: '入場中…',
    privacy:
      '🔒 プライバシーを大切にしています。お客様の個人情報は、ゲーム体験の改善以外の目的では使用いたしません。匿名での参加も可能で、データはいつでも削除できます。',

    qteTitle: 'QTE · 採掘場への夜襲',
    qteBrief: '30秒以内に{n}か所のバルブを閉じろ',
    qteTime: '残り時間',
    qteProgress: '閉鎖',
    qteHint: '現れるバルブを素早くタップ。すべて閉じれば成功',
    qteGo: '襲撃開始',
    qteSuccess: '襲撃成功！2つの採掘場を停止',
    qteFail: '襲撃失敗！番犬に群れが襲われた',
    qteAgain: '再挑戦',

    endingTag: '結末',
    endingProgress: 'あなたの渡りは完結した',
    endingsOf: '全{n}種類の結末',
    revisit: 'すべての選択を終えました',

    netSlowTitle: '通信が低速',
    netSlowBody:
      '自動的に省データモードに切り替えました。再生の安定のため画質を少し下げています。',
    netSlowOk: '了解',
    videoFallback: '動画を読み込み中…',
  },

  fr: {
    title: "Aube de l'Espoir : Oie à tête barrée 2040",
    subtitle: 'Une histoire interactive sur le changement climatique',
    flockStatus: 'État du Vol',
    cooperation: 'Coopération',
    radical: 'Radicalité',
    health: 'Endurance',
    chapterPrefix: 'Chapitre {n}',
    choicePrompt: 'Faites votre choix',
    narrationExpand: 'Afficher tout',
    narrationCollapse: 'Réduire',
    sentOf: '{i}/{n}',
    choiceNowBody: 'Scène terminée — faites votre choix.',
    choiceLater: 'Plus tard',
    conditionNotMet: 'Verrouillé — conditions préalables non remplies',
    effectUnlock: 'Débloqué',
    finalStats: 'Statistiques finales',
    cooperationStat: 'Coopération',
    radicalStat: 'Radicalité',
    healthStat: 'Endurance',
    totalScore: 'Score total',
    scoreGrade: 'Votre rôle',
    restart: 'Recommencer',
    loadingScene: 'Chargement de la scène…',
    chooseScene: 'Simulation des conséquences…',
    langLabel: 'Langue',
    soundOn: 'Activer le son',
    soundOff: 'Muet',

    // Bandeau en direct (visiteurs inclus)
    livePlaying: '{n} en train de jouer',
    livePlayed: '{n} ont joué',

    wechatTitle: 'Avis',
    wechatBody:
      "Vous semblez naviguer dans WeChat. Pour une meilleure lecture vidéo, ouvrez cette page dans votre navigateur par défaut.",
    copyLink: 'Copier le lien',
    copied: 'Lien copié',
    copyFail: 'Copie échouée — appuyez longuement sur la barre d\'adresse',
    copyFailHint: "Ce navigateur bloque le presse-papiers. Appuyez longuement sur la barre d'adresse pour copier.",
    tapToPlay: 'Appuyez pour lire',
    usageTitle: 'Comment ouvrir :',
    usage1: '1. Appuyez sur le menu « … » en haut à droite',
    usage2: '2. Choisissez « Ouvrir dans le navigateur »',
    orLabel: 'Ou :',
    usage3: '1. Appuyez sur « Copier le lien »',
    usage4: '2. Collez le lien dans votre navigateur',
    stayInWechat: 'Continuer dans WeChat',

    welcomeTitle: 'Bienvenue dans Glacier Messenger',
    welcomeSubtitle: 'Avant de commencer, choisissez votre mode de participation',
    anonymous: 'Anonyme',
    nameLabel: 'Nom',
    namePlaceholder: 'Veuillez entrer votre nom',
    emailLabel: 'Email',
    emailOptional: '(optionnel)',
    emailPlaceholder: 'Veuillez entrer votre email (optionnel)',
    emailInvalid: 'Veuillez entrer une adresse email valide',
    startGame: 'Commencer le jeu',
    startAnonymous: 'Commencer anonymement',
    registering: 'Inscription…',
    entering: 'Entrée…',
    privacy:
      "🔒 Nous respectons votre vie privée. Vos informations personnelles sont utilisées uniquement pour améliorer l'expérience de jeu et ne seront pas utilisées à d'autres fins. Vous pouvez jouer anonymement ou supprimer vos données à tout moment.",

    qteTitle: 'QTE · Raid nocturne sur la mine',
    qteBrief: 'Fermez {n} vannes de mine en 30 secondes',
    qteTime: 'Temps restant',
    qteProgress: 'Fermées',
    qteHint: 'Touchez les vannes dès qu’elles apparaissent — fermez-les toutes',
    qteGo: 'Lancer le raid',
    qteSuccess: 'Raid réussi ! Deux mines neutralisées',
    qteFail: 'Raid échoué ! Le vol a été attaqué par les chiens de garde',
    qteAgain: 'Réessayer',

    endingTag: 'Fin',
    endingProgress: 'Votre migration est achevée',
    endingsOf: '{n} fins au total',
    revisit: 'Vous avez fait tous les choix',

    netSlowTitle: 'Réseau lent',
    netSlowBody:
      'Passage automatique en mode économie de données. La qualité est légèrement réduite pour une lecture fluide.',
    netSlowOk: 'Compris',
    videoFallback: 'Chargement de la vidéo…',
  },
}

/**
 * 综合得分评级（合作×0.7 + 体力×0.4 − 激进×0.1，理论区间 −10 ~ 105）
 */
export const GRADES = {
  zh: [
    { min: 80, label: '冰川信使' },
    { min: 62, label: '守护者' },
    { min: 45, label: '同行者' },
    { min: 28, label: '迷途者' },
    { min: -999, label: '旁观者' },
  ],
  en: [
    { min: 80, label: 'Glacier Messenger' },
    { min: 62, label: 'Guardian' },
    { min: 45, label: 'Fellow Traveler' },
    { min: 28, label: 'Wanderer' },
    { min: -999, label: 'Bystander' },
  ],
  ja: [
    { min: 80, label: '氷河の使者' },
    { min: 62, label: '守護者' },
    { min: 45, label: '旅の同行者' },
    { min: 28, label: '迷い鳥' },
    { min: -999, label: '傍観者' },
  ],
  fr: [
    { min: 80, label: 'Messager des Glaciers' },
    { min: 62, label: 'Gardien' },
    { min: 45, label: 'Compagnon de route' },
    { min: 28, label: 'Égaré' },
    { min: -999, label: 'Spectateur' },
  ],
}

/** 取某语言的 UI 串；缺省回落中文 → 键名本身 */
export const makeT = (lang) => {
  const table = UI[lang] || UI[DEFAULT_LANG]
  return (key, vars) => {
    let s = table[key] ?? UI[DEFAULT_LANG][key] ?? key
    if (vars) for (const k of Object.keys(vars)) s = s.replaceAll(`{${k}}`, vars[k])
    return s
  }
}

/** 取某语言的剧情字段（字段需为 {zh,en,ja,fr} 结构） */
export const pick = (obj, lang) => {
  if (obj == null) return ''
  if (typeof obj === 'string') return obj
  return obj[lang] ?? obj[DEFAULT_LANG] ?? ''
}

export const gradeOf = (score, lang) => {
  const list = GRADES[lang] || GRADES[DEFAULT_LANG]
  return (list.find((g) => score >= g.min) || list[list.length - 1]).label
}

/* ───────── 剧情配音（四语）───────── */
export const VO_UI = {
  zh: { label: '剧情旁白', on: '已开启', off: '已关闭', blocked: '点此开启旁白配音', playing: '播放中', skipped: '（镜头提示，不配音）' },
  en: { label: 'Narration', on: 'On', off: 'Off', blocked: 'Tap to enable narration', playing: 'Playing', skipped: '(visual cue, not voiced)' },
  ja: { label: 'ナレーション', on: 'オン', off: 'オフ', blocked: 'タップしてナレーションを有効化', playing: '再生中', skipped: '（映像指示、音声なし）' },
  fr: { label: 'Narration', on: 'Activée', off: 'Désactivée', blocked: 'Appuyez pour activer la narration', playing: 'Lecture', skipped: '(indication visuelle, non doublée)' },
}

export const pickVO = (lang) => VO_UI[lang] || VO_UI[DEFAULT_LANG]
