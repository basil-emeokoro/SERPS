FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web ./apps/web
COPY packages ./packages
RUN npm install --global npm@11.21.0 --no-audit --no-fund
RUN npm ci
# Next.js embeds NEXT_PUBLIC values into browser bundles during the build.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build -w apps/web -- --webpack
RUN npm prune --omit=dev --ignore-scripts --no-audit
FROM node:22-alpine AS runtime
WORKDIR /app
COPY --from=build --chown=node:node /app ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
USER node
EXPOSE 3000
CMD ["npm", "run", "start", "-w", "apps/web", "--", "--hostname", "0.0.0.0"]
