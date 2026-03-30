FROM node:22-alpine

WORKDIR /app

# 依存関係のインストール
COPY package.json ./
RUN npm install

# アプリケーションコードをコピー
COPY . .

# 開発サーバーを起動
CMD ["npm", "run", "dev"]
