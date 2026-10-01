# Binance Alpha 价格告警（无 Docker）

这是一个常驻运行的 Python 服务：定期获取 Binance Alpha 币种价格，以**每天零点后的最新成功价格**为当天基准价；相对基准价上涨或下跌达到设定幅度时，通过 Telegram Bot 发送通知。

默认时区为 `Asia/Shanghai`，因此每天北京时间 `00:00` 会开始新的比较周期。零点后第一次从 Binance 成功取得某个币种价格时，该价格成为当天基准价；在此之前不会发送告警。当天的告警记录也会一并清除，所以新的一天会重新进行涨跌比较。

## 工作规则

- `threshold_percent` 设为 `5` 时，相对当天基准价涨或跌 5%、10%、15% 等新的 5% 档位各通知一次。
- 在 `config.json` 增加币种后，服务的下一轮检查会立刻为它建立基准价；删除币种后不再检查它。
- 修改配置后请重启服务。服务重启会重新以当前价格建立当日基准价。
- 时间由配置中的 `timezone` 控制。VPS 的系统时区无需改成北京时间。

## 配置

复制示例文件并填写 Telegram 信息：

```bash
cp config.example.json config.json
nano config.json
```

示例：

```json
{
  "symbols": ["UB", "AEON", "GRVT"],
  "threshold_percent": 5,
  "check_interval": 10,
  "timezone": "Asia/Shanghai",
  "telegram": {
    "bot_token": "替换为新的 Bot Token",
    "chat_id": "替换为你的 Chat ID"
  }
}
```

`symbols` 中填 Binance Alpha 使用的交易代码。每个代码需要用英文双引号包住，以英文逗号分隔。保存后重启服务：

```bash
sudo systemctl restart alpha-price-alert
sudo systemctl status alpha-price-alert
```

实时查看日志：

```bash
sudo journalctl -u alpha-price-alert -f
```

若日志出现 `XXX not found`，请检查该币种是否已上线，或确认 Binance Alpha 接口使用的正确代码。

## 上传到 GitHub

上传前确认 `config.json` 没有被加入 Git。该文件已在 `.gitignore` 中，里面的 Bot Token 不会被上传。

1. 在 GitHub 网页点击 **New repository**，创建一个空仓库，例如 `alpha-price-alert`。不要勾选 README、`.gitignore` 或 License 初始化选项。
2. 在本项目目录打开 PowerShell，依次执行以下命令。把 `你的GitHub用户名` 改成自己的用户名：

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的GitHub用户名/alpha-price-alert.git
git push -u origin main
```

GitHub 首次推送通常会要求在浏览器完成登录授权。之后每次改完代码可执行：

```powershell
git add .
git commit -m "说明这次修改"
git push
```

如果你曾把真实 Bot Token 上传到任何公开位置，请先在 BotFather 撤销它并生成新 Token。

## 在 Ubuntu/Debian VPS 部署

以下命令将从 GitHub 克隆项目，并以 systemd 服务长期运行。把仓库地址改成你的实际地址：

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
sudo git clone https://github.com/你的GitHub用户名/alpha-price-alert.git /opt/alpha-price-alert
sudo chown -R $USER:$USER /opt/alpha-price-alert
cd /opt/alpha-price-alert
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp config.example.json config.json
nano config.json
```

填写 `config.json` 后，创建并启动服务：

```bash
sed "s/YOUR_LINUX_USER/$USER/g" alpha-price-alert.service | sudo tee /etc/systemd/system/alpha-price-alert.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now alpha-price-alert
sudo systemctl status alpha-price-alert
```

## VPS 一键更新部署

以后本地修改并 `git push` 后，在 VPS 执行下面四行即可拉取并重启。它不会覆盖服务器上的 `config.json`：

```bash
cd /opt/alpha-price-alert
git pull --ff-only
.venv/bin/pip install -r requirements.txt
sudo systemctl restart alpha-price-alert
```

如果仓库设为私有仓库，VPS 需要使用 SSH Deploy Key 或 GitHub Personal Access Token 才能克隆和拉取；公开仓库可直接使用上述 HTTPS 命令。
