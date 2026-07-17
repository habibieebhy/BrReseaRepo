# Stage 1: Build
FROM node:22-alpine AS builder
WORKDIR /app
COPY brixta-dashboard/package*.json ./
RUN npm ci
COPY brixta-dashboard/ .

RUN npm run build

# Stage 2: Runner
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copy built assets from builder
COPY brixta-dashboard/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.ts ./next.config.ts

# Add a non-root user
RUN addgroup -S -g 10001 appgroup && adduser -S -u 10001 appuser -G appgroup
USER 10001:10001

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/login >/dev/null || exit 1
CMD ["npm", "start"]
