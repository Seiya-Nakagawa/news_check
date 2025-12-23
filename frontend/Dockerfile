FROM node:22-alpine

WORKDIR /app

# package.json と package-lock.json をコピー
# ※ まだ存在しない場合はエラーになるため、空のプロジェクト作成後に有効化することを想定
COPY package*.json ./

RUN npm install

# ソースコードをコピー
COPY . .

# 開発用サーバーの起動
CMD ["npm", "run", "dev"]
