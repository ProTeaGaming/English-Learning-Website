// Emoji → stroke-icon name mapping. Category data (shared with the other
// LexiLoop builds) still stores emoji; components resolve them at render time.

const EMOJI_ICON = {
  "➿": "link", "⏳": "hourglass", "◈": "gem", "✈": "plane", "✅": "check-circle",
  "⚠": "alert", "⚡": "zap", "⚖": "scale", "⭐": "star", "🌅": "sun",
  "🌍": "globe", "🌐": "globe", "🌡": "sparkles", "🌦": "cloud", "🌪": "zap",
  "🌱": "sprout", "🌿": "leaf", "🍎": "apple", "🎓": "grad-cap", "🎨": "palette",
  "🎩": "crown", "🎭": "masks", "🎯": "target", "🎲": "dice", "🏃": "activity",
  "🏗": "hard-hat", "🏛": "landmark", "🏥": "cross", "👑": "crown", "💎": "gem",
  "💡": "lightbulb", "💪": "dumbbell", "💬": "message", "💰": "banknote",
  "💻": "monitor", "💼": "briefcase", "📈": "trend-up", "📉": "trend-down",
  "📊": "bar-chart", "📋": "clipboard", "📌": "map-pin", "📏": "ruler",
  "📐": "ruler", "📖": "book-open", "📝": "file-text", "📢": "megaphone",
  "📨": "mail", "📱": "smartphone", "🔄": "rotate", "🔍": "search", "🔑": "key",
  "🔗": "link", "🔥": "flame", "🔧": "wrench", "🔬": "microscope", "🕊": "bird",
  "🖋": "pen", "🗣": "megaphone", "😏": "smile", "🚀": "rocket", "🤔": "compass",
  "🤖": "bot", "🤝": "users", "🧘": "flower", "🧠": "brain", "🧩": "puzzle",
  "🧪": "flask", "🧭": "compass", "🧮": "brain", "🧳": "briefcase",
};

export function iconForEmoji(emoji) {
  return EMOJI_ICON[(emoji || "").replace(/️/g, "")] || "book";
}
