# CCC (Cline Claude Cost)

Ever wonder if you're overpaying for that $200/month Claude Max subscription? CCC analyzes your actual token usage from Cline VS Code extension logs to show you how much you would have paid if you were using Claude API calls instead. Discover your potential savings!

## 🛠️ Requirements

- Python 3.7.0 and above
- VS Code with Cline extension installed
- Some coding history with Cline

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/jeremysltn/CCC.git
   cd CCC
   ```

2. **Install rich**
   ```bash
   pip install rich
   ```

3. **Run the calculator**
   ```bash
   python CCC.py
   ```

## Output

![CCC Demo](https://i.imgur.com/EDU8WM8.jpeg)

## 📁 Where it looks

The script analyzes logs from:
```
~/.vscode-server/data/User/globalStorage/saoudrizwan.claude-dev/tasks/
```

Each Cline project folder contains a `ui_messages.json` file with detailed usage data.

## ⚠️ Important Notes

- API pricing subject to change. Check [Anthropic's official pricing](https://www.anthropic.com/pricing) for current rates.
- **Comparisons with usage limits not included** - Claude Max subscription plans have undisclosed usage limits.

## 💰 Current Claude API Pricing per 1M tokens (Sonnet / Opus)

- **Input tokens**: $3.00 / $15.00
- **Output tokens**: $15.00 / $75.00
- **Cache writes**: $3.75 / $18.75
- **Cache reads**: $0.30 / $1.50

## 🤝 Contributing

Found a bug or want to add a feature? Pull requests welcome!

## 📝 License

MIT License - feel free to use and modify as needed.
