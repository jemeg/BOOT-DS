const DEFAULT_WORDS_AR = [
  "قمر",
  "مفتاح",
  "صقر",
  "محيط",
  "قلعة",
  "زيتون",
  "شراع",
  "منارة",
  "غيمة",
  "نخلة",
  "سيف",
  "جبل",
  "حديقة",
  "سهم",
  "نار",
  "ثلج",
  "مرآة",
  "قطار",
  "مسرح",
  "ورق",
  "بوصلة",
  "حصان",
  "كتاب",
  "مدينة",
  "رعد",
  "صندوق",
  "حوت",
  "كوكب",
  "عين",
  "كنز",
  "لوحة",
  "جسر",
  "برج",
  "عاصفة",
  "مطر",
  "زمرد",
  "سلم",
  "دفتر",
  "غابة",
  "نهر",
  "نمر",
  "ساحة",
  "شهاب",
  "مصباح",
  "مرسى",
  "هواء",
  "قائد",
  "بوابة",
  "خط",
  "هلال",
  "عصفور",
  "سرداب",
  "رسول",
  "شمس",
  "ورد",
  "شعلة",
  "ورشة",
  "ميدالية",
  "زجاج",
  "غروب",
  "صحراء",
  "رؤية",
  "ممر",
  "برق",
  "كأس",
  "أفق",
  "شارع",
  "جرس",
  "مطرقة",
  "رمان",
  "شجرة",
  "نورس",
  "نقش",
  "مستودع"
];

const DEFAULT_WORDS_EN = [
  "Moon",
  "Key",
  "Falcon",
  "Ocean",
  "Castle",
  "Olive",
  "Sail",
  "Lighthouse",
  "Cloud",
  "Palm",
  "Sword",
  "Mountain",
  "Garden",
  "Arrow",
  "Fire",
  "Snow",
  "Mirror",
  "Train",
  "Stage",
  "Paper",
  "Compass",
  "Horse",
  "Book",
  "City",
  "Thunder",
  "Box",
  "Whale",
  "Planet",
  "Eye",
  "Treasure",
  "Bridge",
  "Tower",
  "Storm",
  "Rain",
  "Emerald",
  "Ladder",
  "Notebook",
  "Forest",
  "River",
  "Tiger",
  "Square",
  "Meteor",
  "Lantern",
  "Harbor",
  "Air",
  "Leader",
  "Gate",
  "Line",
  "Crescent",
  "Bird",
  "Cellar",
  "Messenger",
  "Sun",
  "Rose",
  "Flame",
  "Workshop",
  "Medal",
  "Glass",
  "Sunset",
  "Desert",
  "Vision",
  "Path",
  "Lightning",
  "Cup",
  "Horizon",
  "Street",
  "Bell",
  "Hammer",
  "Pomegranate",
  "Tree",
  "Seagull",
  "Engraving",
  "Warehouse"
];

const I18N = {
  ar: {
    newGame: "جولة جديدة",
    restore: "استعادة الجولة",
    clearSave: "مسح الحفظ",
    switchLang: "EN",
    spymasterMode: "وضع رئيس الجواسيس",
    teamRed: "الفريق الأحمر",
    teamBlue: "الفريق الأزرق",
    remaining: "باقي",
    currentTurn: "الدور الحالي",
    subtitle: "فريقان، 25 كلمة، جاسوس واحد في كل فريق. هل ستصل لفريقك قبل القاتل؟",
    statusStart: "اختر كلمة للفريق الحالي.",
    statusTurnRed: "دور الفريق الأحمر: اختر كلمة",
    statusTurnBlue: "دور الفريق الأزرق: اختر كلمة",
    statusWinRed: "الفريق الأحمر فاز!",
    statusWinBlue: "الفريق الأزرق فاز!",
    statusAssassin: "انتهت اللعبة! تم كشف القاتل.",
    hintTitle: "إدخال الدليل",
    clueLabel: "الدليل",
    cluePlaceholder: "حرارة",
    countLabel: "العدد",
    submitHint: "تثبيت الدليل",
    endTurn: "إنهاء الدور",
    timerTitle: "المؤقت",
    timerLabel: "الدقائق لكل دور",
    timerToggle: "تشغيل / إيقاف",
    timerReset: "إعادة ضبط",
    modeTitle: "أوضاع اللعب",
    modeLabel: "اختر الوضع",
    dictionaryTitle: "قاموس الكلمات",
    wordPlaceholder: "اكتب كلمات مفصولة بسطر أو فاصلة",
    applyWords: "تطبيق القائمة",
    resetWords: "إعادة الافتراضي",
    logTitle: "سجل الجولة",
    clearLog: "مسح السجل",
    boardTitle: "إعدادات اللوحة",
    boardSizeLabel: "حجم اللوحة",
    redCountLabel: "عدد الأحمر",
    blueCountLabel: "عدد الأزرق",
    spymasterCodeLabel: "رمز رئيس الجواسيس",
    neutralLabel: "المحايد",
    footerText: "لعبة محلية داخل المتصفح. يمكنك مشاركة الشاشة للعب جماعي، أو إضافة قواعدك الخاصة.",
    hintDisplay: "الدليل",
    modeClassic: "كلاسيكي",
    modeFast: "سريع",
    modeStealth: "خفاء",
    modePractice: "تدريب",
    modeDescClassic: "الوضع الأساسي مع مؤقت قياسي.",
    modeDescFast: "مؤقت أقصر للجولات السريعة.",
    modeDescStealth: "يخفي ألوان البطاقات بعد الكشف.",
    modeDescPractice: "تدريب فردي بلا فريق أزرق.",
    logHint: "تم تثبيت الدليل",
    logReveal: "كشف",
    logTurn: "تبديل الدور",
    logTimer: "انتهى الوقت",
    logNewGame: "بدء جولة جديدة",
    logRestore: "تمت استعادة الجولة",
    logClear: "تم مسح السجل",
    spectator: "وضع المشاهد",
    highContrast: "تباين عالي",
    sound: "الصوت",
    playersTitle: "إدارة اللاعبين",
    redSpymaster: "رئيس الجواسيس الأحمر",
    blueSpymaster: "رئيس الجواسيس الأزرق",
    score: "النقاط",
    round: "الجولة",
    duetMode: "وضع الثنائي",
    speedrunMode: "تحدي الوقت",
    shareTitle: "مشاركة اللعبة",
    shareUrl: "نسخ الرابط",
    screenshot: "لقطة شاشة",
    exportLog: "تصدير السجل",
    statsTitle: "إحصائيات اللعب",
    gamesPlayed: "الجولات",
    redWins: "فوز الأحمر",
    blueWins: "فوز الأزرق",
    bestTime: "أسرع فوز",
    topClues: "أكثر الأدلة استخداماً",
    resetStats: "إعادة تعيين",
    undo: "تراجع",
    redo: "إعادة",
    tutorial: "دليل تعليمي",
    tutorialTitle: "كيفية اللعب",
    tutorialStep1: "رئيس الجواسيس يعطي دليلاً (كلمة + رقم) يصف كلمات فريقه",
    tutorialStep2: "الفريق يحاول تخمين الكلمات الصحيحة بناءً على الدليل",
    tutorialStep3: "تجنب كشف كلمات الفريق الآخر أو القاتل (الأسود)",
    tutorialStep4: "أول فريق يكشف كل كلماته يفوز!",
    keyboardShortcuts: "اختصارات الكيبورد",
    shortcutEndTurn: "إنهاء الدور",
    shortcutUndo: "تراجع",
    shortcutRedo: "إعادة",
    shortcutNewGame: "جولة جديدة",
    shortcutSpymaster: "تبديل رئيس الجواسيس",
    shortcutTimer: "تشغيل/إيقاف المؤقت",
    shortcutCards: "اختيار بطاقة",
    clueWarning: "تحذير: الدليل موجود على اللوحة!",
    dismiss: "تجاهل"
  },
  en: {
    newGame: "New Round",
    restore: "Restore",
    clearSave: "Clear Save",
    switchLang: "AR",
    spymasterMode: "Spymaster Mode",
    teamRed: "Red Team",
    teamBlue: "Blue Team",
    remaining: "Remaining",
    currentTurn: "Current Turn",
    subtitle: "Two teams, 25 cards, one assassin. Can you reach your agents first?",
    statusStart: "Pick a word for the current team.",
    statusTurnRed: "Red team's turn: pick a word",
    statusTurnBlue: "Blue team's turn: pick a word",
    statusWinRed: "Red team wins!",
    statusWinBlue: "Blue team wins!",
    statusAssassin: "Game over! The assassin was revealed.",
    hintTitle: "Clue Input",
    clueLabel: "Clue",
    cluePlaceholder: "Heat",
    countLabel: "Count",
    submitHint: "Lock Clue",
    endTurn: "End Turn",
    timerTitle: "Timer",
    timerLabel: "Minutes per turn",
    timerToggle: "Start / Pause",
    timerReset: "Reset",
    modeTitle: "Game Modes",
    modeLabel: "Choose mode",
    dictionaryTitle: "Word Bank",
    wordPlaceholder: "Enter words separated by commas or lines",
    applyWords: "Apply List",
    resetWords: "Reset Default",
    logTitle: "Round Log",
    clearLog: "Clear Log",
    boardTitle: "Board Settings",
    boardSizeLabel: "Board size",
    redCountLabel: "Red cards",
    blueCountLabel: "Blue cards",
    spymasterCodeLabel: "Spymaster code",
    neutralLabel: "Neutral",
    footerText: "Local browser game. Share your screen and add your own rules.",
    hintDisplay: "Clue",
    modeClassic: "Classic",
    modeFast: "Speed",
    modeStealth: "Stealth",
    modePractice: "Practice",
    modeDescClassic: "Balanced classic play with a standard timer.",
    modeDescFast: "Shorter timer for quick rounds.",
    modeDescStealth: "Hide revealed colors from guessers.",
    modeDescPractice: "Solo training without the blue team.",
    logHint: "Clue locked",
    logReveal: "Revealed",
    logTurn: "Turn switched",
    logTimer: "Timer ended",
    logNewGame: "New round started",
    logRestore: "Round restored",
    logClear: "Log cleared",
    spectator: "Spectator",
    highContrast: "High Contrast",
    sound: "Sound",
    playersTitle: "Player Management",
    redSpymaster: "Red Spymaster",
    blueSpymaster: "Blue Spymaster",
    score: "Score",
    round: "Round",
    duetMode: "Duet Mode",
    speedrunMode: "Speedrun",
    shareTitle: "Share Game",
    shareUrl: "Copy URL",
    screenshot: "Screenshot",
    exportLog: "Export Log",
    statsTitle: "Game Statistics",
    gamesPlayed: "Games",
    redWins: "Red Wins",
    blueWins: "Blue Wins",
    bestTime: "Best Time",
    topClues: "Top Clues",
    resetStats: "Reset Stats",
    undo: "Undo",
    redo: "Redo",
    tutorial: "Tutorial",
    tutorialTitle: "How to Play",
    tutorialStep1: "Spymaster gives a clue (word + number) describing their team's words",
    tutorialStep2: "Team tries to guess the correct words based on the clue",
    tutorialStep3: "Avoid revealing the other team's words or the assassin (black)",
    tutorialStep4: "First team to reveal all their words wins!",
    keyboardShortcuts: "Keyboard Shortcuts",
    shortcutEndTurn: "End turn",
    shortcutUndo: "Undo",
    shortcutRedo: "Redo",
    shortcutNewGame: "New game",
    shortcutSpymaster: "Toggle spymaster",
    shortcutTimer: "Toggle timer",
    shortcutCards: "Select card",
    clueWarning: "Warning: Clue exists on the board!",
    dismiss: "Dismiss"
  }
};

const MODE_PRESETS = [
  { id: "classic", timerMinutes: 3, stealth: false, practice: false },
  { id: "fast", timerMinutes: 2, stealth: false, practice: false },
  { id: "stealth", timerMinutes: 3, stealth: true, practice: false },
  { id: "practice", timerMinutes: 0, stealth: false, practice: true }
];

const boardEl = document.getElementById("board");
const redRemainingEl = document.getElementById("redRemaining");
const blueRemainingEl = document.getElementById("blueRemaining");
const currentTurnEl = document.getElementById("currentTurn");
const statusMessageEl = document.getElementById("statusMessage");
const timerDisplayEl = document.getElementById("timerDisplay");
const hintDisplayEl = document.getElementById("hintDisplay");
const newGameBtn = document.getElementById("newGameBtn");
const restoreGameBtn = document.getElementById("restoreGameBtn");
const clearSaveBtn = document.getElementById("clearSaveBtn");
const langToggleBtn = document.getElementById("langToggle");
const spymasterToggle = document.getElementById("spymasterToggle");
const clueInput = document.getElementById("clueInput");
const countInput = document.getElementById("countInput");
const submitHintBtn = document.getElementById("submitHintBtn");
const endTurnBtn = document.getElementById("endTurnBtn");
const timerMinutesInput = document.getElementById("timerMinutes");
const timerToggleBtn = document.getElementById("timerToggleBtn");
const resetTimerBtn = document.getElementById("resetTimerBtn");
const modeSelect = document.getElementById("modeSelect");
const modeDescriptionEl = document.getElementById("modeDescription");
const wordListInput = document.getElementById("wordListInput");
const applyWordsBtn = document.getElementById("applyWordsBtn");
const resetWordsBtn = document.getElementById("resetWordsBtn");
const logListEl = document.getElementById("logList");
const clearLogBtn = document.getElementById("clearLogBtn");
const boardSizeSelect = document.getElementById("boardSizeSelect");
const redCountInput = document.getElementById("redCountInput");
const blueCountInput = document.getElementById("blueCountInput");
const neutralCountEl = document.getElementById("neutralCount");
const spymasterCodeInput = document.getElementById("spymasterCode");

let state = null;
let timerInterval = null;

const STORAGE_KEY = "codenames_state_v1";

const t = (key) => I18N[state.language][key] || key;

const shuffle = (array) => {
  const copy = [...array];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
};

const parseWords = (text) =>
  text
    .split(/\n|,|،/)
    .map((word) => word.trim())
    .filter((word) => word.length > 1);

const getModePreset = (modeId) =>
  MODE_PRESETS.find((preset) => preset.id === modeId) || MODE_PRESETS[0];

const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remaining).padStart(2, "0")}`;
};

const updateLanguage = () => {
  document.documentElement.lang = state.language;
  document.documentElement.dir = state.language === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    const value = I18N[state.language][key];
    if (value) {
      el.textContent = value;
    }
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    const value = I18N[state.language][key];
    if (value) {
      el.setAttribute("placeholder", value);
    }
  });
  langToggleBtn.textContent = t("switchLang");
  renderModeOptions();
  updateStatus();
  renderHint();
  renderLog();
};

const renderModeOptions = () => {
  modeSelect.innerHTML = "";
  MODE_PRESETS.forEach((preset) => {
    const option = document.createElement("option");
    option.value = preset.id;
    option.textContent = t(`mode${preset.id.charAt(0).toUpperCase()}${preset.id.slice(1)}`);
    modeSelect.appendChild(option);
  });
  modeSelect.value = state.mode;
  modeDescriptionEl.textContent = t(`modeDesc${state.mode.charAt(0).toUpperCase()}${state.mode.slice(1)}`);
};

const updateCountsFromInputs = () => {
  const size = Number(boardSizeSelect.value);
  const total = size * size;
  let red = Number(redCountInput.value) || 1;
  let blue = Number(blueCountInput.value) || 0;

  red = Math.max(1, Math.min(red, total - 2));
  blue = Math.max(0, Math.min(blue, total - 1 - red));

  if (getModePreset(state.mode).practice) {
    blue = 0;
  }

  const neutral = Math.max(0, total - red - blue - 1);
  redCountInput.value = red;
  blueCountInput.value = blue;
  neutralCountEl.textContent = neutral;

  return { red, blue, neutral, assassin: 1, total };
};

const buildRoles = (counts) => {
  const roles = [
    ...Array(counts.red).fill("red"),
    ...Array(counts.blue).fill("blue"),
    ...Array(counts.neutral).fill("neutral"),
    "assassin"
  ];
  return shuffle(roles);
};

const pickWords = (total) => {
  const base = state.customWords.length ? state.customWords : state.dictionary;
  const combined = [...new Set([...base, ...state.dictionary])];
  if (combined.length < total) {
    return shuffle([...combined, ...state.dictionary]).slice(0, total);
  }
  return shuffle(combined).slice(0, total);
};

const renderBoard = () => {
  boardEl.innerHTML = "";
  boardEl.style.gridTemplateColumns = `repeat(${state.boardSize}, minmax(110px, 1fr))`;
  state.cards.forEach((card, index) => {
    const cardEl = document.createElement("button");
    cardEl.className = "card";
    cardEl.type = "button";
    cardEl.dataset.index = index;

    const label = document.createElement("span");
    label.textContent = card.word;
    cardEl.appendChild(label);

    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = card.role;
    cardEl.appendChild(tag);

    if (state.spymaster) {
      cardEl.classList.add("spymaster");
    }

    if (card.revealed) {
      cardEl.classList.add("revealed", card.role);
    }

    cardEl.addEventListener("click", handleCardClick);
    boardEl.appendChild(cardEl);
  });
};

const updateStatus = () => {
  redRemainingEl.textContent = state.remaining.red;
  blueRemainingEl.textContent = state.remaining.blue;
  currentTurnEl.textContent = state.turn === "red" ? t("teamRed") : t("teamBlue");

  if (state.gameOver) {
    statusMessageEl.textContent = state.gameOver;
    return;
  }

  statusMessageEl.textContent =
    state.turn === "red" ? t("statusTurnRed") : t("statusTurnBlue");
};

const renderHint = () => {
  if (!state.hint) {
    hintDisplayEl.textContent = "";
    return;
  }
  hintDisplayEl.textContent = `${t("hintDisplay")}: ${state.hint.clue} (${state.hint.count})`;
};

const renderLog = () => {
  logListEl.innerHTML = "";
  state.log.slice(-40).forEach((entry) => {
    const item = document.createElement("li");
    item.textContent = entry;
    logListEl.appendChild(item);
  });
};

const addLog = (entry) => {
  state.log.push(entry);
  renderLog();
};

const setGameOver = (message) => {
  state.gameOver = message;
  stopTimer();
};

const switchTurn = () => {
  if (getModePreset(state.mode).practice) {
    state.turn = "red";
    return;
  }
  state.turn = state.turn === "red" ? "blue" : "red";
  state.hint = null;
  resetTimer();
  addLog(`${t("logTurn")}: ${state.turn === "red" ? t("teamRed") : t("teamBlue")}`);
};

const handleCardClick = (event) => {
  const index = Number(event.currentTarget.dataset.index);
  const card = state.cards[index];

  if (state.gameOver || card.revealed) {
    return;
  }

  card.revealed = true;
  addLog(`${t("logReveal")}: ${card.word}`);

  if (card.role === "assassin") {
    setGameOver(t("statusAssassin"));
  } else if (card.role === "red" || card.role === "blue") {
    state.remaining[card.role] -= 1;
    if (state.remaining[card.role] === 0) {
      setGameOver(card.role === "red" ? t("statusWinRed") : t("statusWinBlue"));
    }
  }

  if (!state.gameOver) {
    if (card.role !== state.turn) {
      switchTurn();
    }
  }

  renderBoard();
  updateStatus();
  renderHint();
  persistGame();
};

const resetTimer = () => {
  const minutes = Number(timerMinutesInput.value) || 0;
  state.timerSeconds = minutes * 60;
  timerDisplayEl.textContent = formatTime(state.timerSeconds);
};

const startTimer = () => {
  if (timerInterval || state.timerSeconds <= 0 || state.gameOver) {
    return;
  }
  timerInterval = setInterval(() => {
    state.timerSeconds -= 1;
    timerDisplayEl.textContent = formatTime(state.timerSeconds);
    if (state.timerSeconds <= 0) {
      handleTimerEnd();
    }
  }, 1000);
};

const stopTimer = () => {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
};

const handleTimerEnd = () => {
  stopTimer();
  playBeep();
  addLog(t("logTimer"));
  if (!state.gameOver) {
    switchTurn();
    renderBoard();
    updateStatus();
    renderHint();
  }
};

const playBeep = () => {
  if (!window.AudioContext) return;
  const context = new AudioContext();
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = "triangle";
  oscillator.frequency.value = 740;
  gain.gain.value = 0.12;
  oscillator.connect(gain);
  gain.connect(context.destination);
  oscillator.start();
  oscillator.stop(context.currentTime + 0.2);
};

const persistGame = () => {
  const payload = {
    ...state,
    timerRunning: Boolean(timerInterval)
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
};

const restoreGame = () => {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return;
  const saved = JSON.parse(raw);
  state = {
    ...saved,
    dictionary: saved.dictionary || DEFAULT_WORDS_AR,
    customWords: saved.customWords || [],
    log: saved.log || []
  };
  syncInputsFromState();
  updateLanguage();
  renderBoard();
  updateStatus();
  renderHint();
  renderLog();
  document.body.classList.toggle("mode-stealth", getModePreset(state.mode).stealth);
  resetTimer();
  if (saved.timerRunning) {
    startTimer();
  }
  addLog(t("logRestore"));
};

const clearSave = () => {
  localStorage.removeItem(STORAGE_KEY);
};

const syncInputsFromState = () => {
  modeSelect.value = state.mode;
  boardSizeSelect.value = String(state.boardSize);
  redCountInput.value = state.counts.red;
  blueCountInput.value = state.counts.blue;
  neutralCountEl.textContent = state.counts.neutral;
  timerMinutesInput.value = state.timerMinutes;
  wordListInput.value = state.customWords.join("\n");
};

const applySettings = () => {
  const counts = updateCountsFromInputs();
  state.counts = counts;
  state.boardSize = Number(boardSizeSelect.value);
  state.timerMinutes = Number(timerMinutesInput.value) || 0;
  resetTimer();
  document.body.classList.toggle("mode-stealth", getModePreset(state.mode).stealth);
};

const startGame = () => {
  applySettings();
  const totalCards = state.boardSize * state.boardSize;
  const roles = buildRoles(state.counts);
  const words = pickWords(totalCards);
  state.cards = words.map((word, index) => ({
    word,
    role: roles[index],
    revealed: false
  }));
  state.turn = "red";
  state.remaining = { red: state.counts.red, blue: state.counts.blue };
  state.gameOver = null;
  state.hint = null;
  state.log = [];
  resetTimer();
  stopTimer();

  renderBoard();
  updateStatus();
  renderHint();
  renderLog();
  addLog(t("logNewGame"));
  persistGame();
};

const handleSubmitHint = () => {
  const clue = clueInput.value.trim();
  const count = Number(countInput.value) || 1;
  if (!clue) return;
  state.hint = { clue, count };
  addLog(`${t("logHint")}: ${clue} (${count})`);
  renderHint();
  persistGame();
};

const handleEndTurn = () => {
  if (state.gameOver) return;
  switchTurn();
  renderBoard();
  updateStatus();
  renderHint();
  persistGame();
};

const handleModeChange = () => {
  state.mode = modeSelect.value;
  const preset = getModePreset(state.mode);
  timerMinutesInput.value = preset.timerMinutes;
  modeDescriptionEl.textContent = t(`modeDesc${state.mode.charAt(0).toUpperCase()}${state.mode.slice(1)}`);
  startGame();
};

const handleWordApply = () => {
  const parsed = parseWords(wordListInput.value);
  state.customWords = parsed;
  startGame();
};

const handleWordReset = () => {
  state.customWords = [];
  wordListInput.value = "";
  startGame();
};

const toggleSpymaster = () => {
  if (spymasterToggle.checked && spymasterCodeInput.value) {
    const attempt = window.prompt(t("spymasterCodeLabel"));
    if (attempt !== spymasterCodeInput.value) {
      spymasterToggle.checked = false;
      return;
    }
  }
  state.spymaster = spymasterToggle.checked;
  renderBoard();
  persistGame();
};

const handleLangToggle = () => {
  state.language = state.language === "ar" ? "en" : "ar";
  state.dictionary = state.language === "ar" ? DEFAULT_WORDS_AR : DEFAULT_WORDS_EN;
  updateLanguage();
  startGame();
};

const handleTimerToggle = () => {
  if (timerInterval) {
    stopTimer();
  } else {
    startTimer();
  }
};

const handleTimerReset = () => {
  stopTimer();
  resetTimer();
};

const handleClearLog = () => {
  state.log = [];
  renderLog();
  addLog(t("logClear"));
};

const initState = () => {
  state = {
    language: "ar",
    mode: "classic",
    dictionary: DEFAULT_WORDS_AR,
    customWords: [],
    boardSize: 5,
    counts: { red: 9, blue: 8, neutral: 7, assassin: 1 },
    cards: [],
    remaining: { red: 9, blue: 8 },
    turn: "red",
    spymaster: false,
    timerSeconds: 180,
    timerMinutes: 3,
    hint: null,
    log: [],
    gameOver: null
  };
};

const init = () => {
  initState();
  renderModeOptions();
  updateCountsFromInputs();
  updateLanguage();
  startGame();
};

newGameBtn.addEventListener("click", startGame);
restoreGameBtn.addEventListener("click", restoreGame);
clearSaveBtn.addEventListener("click", clearSave);
langToggleBtn.addEventListener("click", handleLangToggle);
spymasterToggle.addEventListener("change", toggleSpymaster);
submitHintBtn.addEventListener("click", handleSubmitHint);
endTurnBtn.addEventListener("click", handleEndTurn);
timerToggleBtn.addEventListener("click", handleTimerToggle);
resetTimerBtn.addEventListener("click", handleTimerReset);
modeSelect.addEventListener("change", handleModeChange);
applyWordsBtn.addEventListener("click", handleWordApply);
resetWordsBtn.addEventListener("click", handleWordReset);
clearLogBtn.addEventListener("click", handleClearLog);
boardSizeSelect.addEventListener("change", startGame);
redCountInput.addEventListener("change", startGame);
blueCountInput.addEventListener("change", startGame);

// ===== الميزات الجديدة =====

// عناصر DOM الجديدة
const redSpymasterInput = document.getElementById("redSpymaster");
const blueSpymasterInput = document.getElementById("blueSpymaster");
const redScoreEl = document.getElementById("redScore");
const blueScoreEl = document.getElementById("blueScore");
const redSpymasterDisplay = document.getElementById("redSpymasterDisplay");
const blueSpymasterDisplay = document.getElementById("blueSpymasterDisplay");
const roundNumberEl = document.getElementById("roundNumber");
const gamesPlayedEl = document.getElementById("gamesPlayed");
const redWinsEl = document.getElementById("redWins");
const blueWinsEl = document.getElementById("blueWins");
const bestTimeEl = document.getElementById("bestTime");
const topCluesList = document.getElementById("topCluesList");
const resetStatsBtn = document.getElementById("resetStatsBtn");
const shareUrlBtn = document.getElementById("shareUrlBtn");
const screenshotBtn = document.getElementById("screenshotBtn");
const exportLogBtn = document.getElementById("exportLogBtn");
const undoBtn = document.getElementById("undoBtn");
const redoBtn = document.getElementById("redoBtn");
const spectatorBtn = document.getElementById("spectatorBtn");
const highContrastBtn = document.getElementById("highContrastBtn");
const soundToggle = document.getElementById("soundToggle");
const tutorialBtn = document.getElementById("tutorialBtn");
const tutorialModal = document.getElementById("tutorialModal");
const closeTutorial = document.getElementById("closeTutorial");
const clueWarning = document.getElementById("clueWarning");
const dismissWarning = document.getElementById("dismissWarning");
const duetModeCheckbox = document.getElementById("duetMode");
const speedrunModeCheckbox = document.getElementById("speedrunMode");

// حالة التراجع/الإعادة
let history = [];
let historyIndex = -1;
const MAX_HISTORY = 50;

// الإحصائيات
let stats = {
  gamesPlayed: 0,
  redWins: 0,
  blueWins: 0,
  bestTime: null,
  clues: {}
};

// تحميل الإحصائيات
const loadStats = () => {
  const saved = localStorage.getItem("codenames_stats_v1");
  if (saved) {
    stats = JSON.parse(saved);
    renderStats();
  }
};

// حفظ الإحصائيات
const saveStats = () => {
  localStorage.setItem("codenames_stats_v1", JSON.stringify(stats));
};

// عرض الإحصائيات
const renderStats = () => {
  if (gamesPlayedEl) gamesPlayedEl.textContent = stats.gamesPlayed;
  if (redWinsEl) redWinsEl.textContent = stats.redWins;
  if (blueWinsEl) blueWinsEl.textContent = stats.blueWins;
  if (bestTimeEl) bestTimeEl.textContent = stats.bestTime ? formatTime(stats.bestTime) : "-";
  
  // عرض أكثر الأدلة استخداماً
  if (topCluesList) {
    topCluesList.innerHTML = "";
    const sortedClues = Object.entries(stats.clues)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
    sortedClues.forEach(([clue, count]) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${clue}</span><span class="clue-count">${count}</span>`;
      topCluesList.appendChild(li);
    });
  }
};

// تحديث الإحصائيات عند الفوز
const updateStats = (winner) => {
  stats.gamesPlayed++;
  if (winner === "red") stats.redWins++;
  if (winner === "blue") stats.blueWins++;
  
  // حساب وقت اللعبة
  if (state.startTime) {
    const gameTime = Math.floor((Date.now() - state.startTime) / 1000);
    if (!stats.bestTime || gameTime < stats.bestTime) {
      stats.bestTime = gameTime;
    }
  }
  
  saveStats();
  renderStats();
};

// تتبع الأدلة
const trackClue = (clue) => {
  if (!clue) return;
  stats.clues[clue] = (stats.clues[clue] || 0) + 1;
  saveStats();
  renderStats();
};

// حفظ في التاريخ للتراجع
const saveToHistory = () => {
  // إزالة أي إدخالات بعد المؤشر الحالي
  history = history.slice(0, historyIndex + 1);
  
  // إضافة الحالة الحالية
  history.push(JSON.parse(JSON.stringify({
    cards: state.cards,
    turn: state.turn,
    remaining: state.remaining,
    hint: state.hint,
    gameOver: state.gameOver
  })));
  
  // الحد من حجم التاريخ
  if (history.length > MAX_HISTORY) {
    history.shift();
  } else {
    historyIndex++;
  }
  
  updateUndoRedoButtons();
};

// تحديث أزرار التراجع/الإعادة
const updateUndoRedoButtons = () => {
  if (undoBtn) undoBtn.disabled = historyIndex <= 0;
  if (redoBtn) redoBtn.disabled = historyIndex >= history.length - 1;
};

// تراجع
const undo = () => {
  if (historyIndex > 0) {
    historyIndex--;
    restoreFromHistory();
  }
};

// إعادة
const redo = () => {
  if (historyIndex < history.length - 1) {
    historyIndex++;
    restoreFromHistory();
  }
};

// استعادة من التاريخ
const restoreFromHistory = () => {
  const saved = history[historyIndex];
  state.cards = saved.cards;
  state.turn = saved.turn;
  state.remaining = saved.remaining;
  state.hint = saved.hint;
  state.gameOver = saved.gameOver;
  
  renderBoard();
  updateStatus();
  renderHint();
  updateUndoRedoButtons();
  persistGame();
};

// التحقق من الدليل
const validateClue = (clue) => {
  if (!clue) return true;
  const lowerClue = clue.toLowerCase();
  const existsOnBoard = state.cards.some(card => 
    card.word.toLowerCase() === lowerClue || 
    card.word.toLowerCase().includes(lowerClue) ||
    lowerClue.includes(card.word.toLowerCase())
  );
  return !existsOnBoard;
};

// إظهار/إخفاء تحذير الدليل
const showClueWarning = () => {
  if (clueWarning) clueWarning.classList.add("active");
};

const hideClueWarning = () => {
  if (clueWarning) clueWarning.classList.remove("active");
};

// تأثيرات الاحتفال
const triggerConfetti = () => {
  const container = document.getElementById("confetti-container");
  if (!container) return;
  
  const colors = ["#d4534b", "#2f61c2", "#d9a441", "#1f1f1f"];
  
  for (let i = 0; i < 100; i++) {
    const confetti = document.createElement("div");
    confetti.className = "confetti";
    confetti.style.left = Math.random() * 100 + "%";
    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    confetti.style.animationDelay = Math.random() * 2 + "s";
    container.appendChild(confetti);
    
    setTimeout(() => confetti.remove(), 3000);
  }
};

// تأثيرات صوتية محسنة
const playSound = (type) => {
  if (!soundToggle || !soundToggle.checked) return;
  if (!window.AudioContext) return;
  
  const ctx = new AudioContext();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  
  osc.connect(gain);
  gain.connect(ctx.destination);
  
  switch (type) {
    case "reveal":
      osc.type = "sine";
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(660, ctx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.2);
      break;
    case "win":
      osc.type = "triangle";
      osc.frequency.setValueAtTime(523, ctx.currentTime);
      osc.frequency.setValueAtTime(659, ctx.currentTime + 0.1);
      osc.frequency.setValueAtTime(784, ctx.currentTime + 0.2);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.5);
      break;
    case "lose":
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(200, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(100, ctx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.3);
      break;
    case "timer":
      osc.type = "triangle";
      osc.frequency.setValueAtTime(800, ctx.currentTime);
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.2);
      break;
  }
};

// مشاركة اللعبة
const shareGameUrl = () => {
  const gameState = btoa(JSON.stringify({
    cards: state.cards,
    turn: state.turn,
    remaining: state.remaining,
    hint: state.hint
  }));
  const url = `${window.location.origin}${window.location.pathname}?game=${gameState}`;
  navigator.clipboard.writeText(url).then(() => {
    alert(t("shareUrl") + " - " + (state.language === "ar" ? "تم النسخ!" : "Copied!"));
  });
};

// لقطة شاشة
const takeScreenshot = () => {
  alert(t("screenshot") + " - " + (state.language === "ar" ? "استخدم مفتاح Print Screen" : "Use Print Screen key"));
};

// تصدير السجل
const exportLog = () => {
  const logText = state.log.join("\n");
  const blob = new Blob([logText], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `codenames-log-${new Date().toISOString().slice(0, 10)}.txt`;
  a.click();
  URL.revokeObjectURL(url);
};

// وضع المشاهد
const toggleSpectatorMode = () => {
  document.body.classList.toggle("spectator-mode");
  const isSpectator = document.body.classList.contains("spectator-mode");
  spectatorBtn.textContent = isSpectator ? t("spectator") + " ✓" : t("spectator");
};

// التباين العالي
const toggleHighContrast = () => {
  document.body.classList.toggle("high-contrast");
  const isHighContrast = document.body.classList.contains("high-contrast");
  highContrastBtn.textContent = isHighContrast ? t("highContrast") + " ✓" : t("highContrast");
};

// التعليمي
const openTutorial = () => {
  if (tutorialModal) tutorialModal.classList.add("active");
};

const closeTutorialModal = () => {
  if (tutorialModal) tutorialModal.classList.remove("active");
};

// اختصارات الكيبورد
document.addEventListener("keydown", (e) => {
  // التراجع
  if (e.ctrlKey && e.key === "z" && !e.shiftKey) {
    e.preventDefault();
    undo();
    return;
  }
  
  // الإعادة
  if ((e.ctrlKey && e.key === "y") || (e.ctrlKey && e.shiftKey && e.key === "Z")) {
    e.preventDefault();
    redo();
    return;
  }
  
  // جولة جديدة
  if (e.key === "n" || e.key === "N") {
    if (!e.ctrlKey && !e.altKey && !e.metaKey) {
      startGame();
      return;
    }
  }
  
  // إنهاء الدور
  if (e.key === " " || e.key === "Space") {
    e.preventDefault();
    handleEndTurn();
    return;
  }
  
  // تبديل رئيس الجواسيس
  if (e.key === "s" || e.key === "S") {
    if (!e.ctrlKey && !e.altKey && !e.metaKey) {
      spymasterToggle.checked = !spymasterToggle.checked;
      toggleSpymaster();
      return;
    }
  }
  
  // المؤقت
  if (e.key === "t" || e.key === "T") {
    if (!e.ctrlKey && !e.altKey && !e.metaKey) {
      handleTimerToggle();
      return;
    }
  }
  
  // اختيار بطاقة بالأرقام
  if (e.key >= "1" && e.key <= "9") {
    const index = parseInt(e.key) - 1;
    if (state.cards[index] && !state.cards[index].revealed) {
      handleCardClick({ currentTarget: { dataset: { index: String(index) } } });
    }
  }
  
  // إغلاق النافذة المنبثقة
  if (e.key === "Escape") {
    closeTutorialModal();
    hideClueWarning();
  }
});

// معالجي الأحداث الجديدة
if (redSpymasterInput) {
  redSpymasterInput.addEventListener("input", () => {
    if (redSpymasterDisplay) redSpymasterDisplay.textContent = redSpymasterInput.value || "-";
  });
}

if (blueSpymasterInput) {
  blueSpymasterInput.addEventListener("input", () => {
    if (blueSpymasterDisplay) blueSpymasterDisplay.textContent = blueSpymasterInput.value || "-";
  });
}

if (resetStatsBtn) resetStatsBtn.addEventListener("click", () => {
  stats = { gamesPlayed: 0, redWins: 0, blueWins: 0, bestTime: null, clues: {} };
  saveStats();
  renderStats();
});

if (shareUrlBtn) shareUrlBtn.addEventListener("click", shareGameUrl);
if (screenshotBtn) screenshotBtn.addEventListener("click", takeScreenshot);
if (exportLogBtn) exportLogBtn.addEventListener("click", exportLog);
if (undoBtn) undoBtn.addEventListener("click", undo);
if (redoBtn) redoBtn.addEventListener("click", redo);
if (spectatorBtn) spectatorBtn.addEventListener("click", toggleSpectatorMode);
if (highContrastBtn) highContrastBtn.addEventListener("click", toggleHighContrast);
if (tutorialBtn) tutorialBtn.addEventListener("click", openTutorial);
if (closeTutorial) closeTutorial.addEventListener("click", closeTutorialModal);
if (dismissWarning) dismissWarning.addEventListener("click", hideClueWarning);

// إغلاق النافذة المنبثقة بالنقر خارجها
if (tutorialModal) {
  tutorialModal.addEventListener("click", (e) => {
    if (e.target === tutorialModal) closeTutorialModal();
  });
}

// تحديث handleSubmitHint للتحقق من الدليل وتتبعه
const originalHandleSubmitHint = handleSubmitHint;
handleSubmitHint = () => {
  const clue = clueInput.value.trim();
  
  if (!validateClue(clue)) {
    showClueWarning();
    return;
  }
  
  hideClueWarning();
  originalHandleSubmitHint();
  trackClue(clue);
  saveToHistory();
};

// تحديث handleCardClick للصوت والتاريخ
const originalHandleCardClick = handleCardClick;
handleCardClick = (event) => {
  const index = Number(event.currentTarget.dataset.index);
  const card = state.cards[index];
  
  if (state.gameOver || card.revealed) return;
  
  saveToHistory();
  originalHandleCardClick(event);
  playSound("reveal");
  
  if (state.gameOver) {
    triggerConfetti();
    const winner = state.remaining.red === 0 ? "red" : state.remaining.blue === 0 ? "blue" : null;
    if (winner) {
      updateStats(winner);
      playSound("win");
    } else {
      playSound("lose");
    }
  }
};

// تحديث startGame
const originalStartGame = startGame;
startGame = () => {
  originalStartGame();
  state.startTime = Date.now();
  state.round = (state.round || 0) + 1;
  if (roundNumberEl) roundNumberEl.textContent = state.round;
  history = [];
  historyIndex = -1;
  saveToHistory();
  hideClueWarning();
};

// تحميل اللعبة من URL
const loadFromUrl = () => {
  const params = new URLSearchParams(window.location.search);
  const gameData = params.get("game");
  if (gameData) {
    try {
      const saved = JSON.parse(atob(gameData));
      state.cards = saved.cards;
      state.turn = saved.turn;
      state.remaining = saved.remaining;
      state.hint = saved.hint;
      renderBoard();
      updateStatus();
      renderHint();
    } catch (e) {
      console.error("Failed to load game from URL", e);
    }
  }
};

// تهيئة
loadStats();
loadFromUrl();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("service-worker.js");
  });
}

init();
