FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
COPY apps/web ./apps/web
COPY packages ./packages
RUN npm install
RUN npm run build -w apps/web
EXPOSE 3000
CMD ["npm", "run", "start", "-w", "apps/web"]
