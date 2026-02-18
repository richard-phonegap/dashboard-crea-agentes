FROM node:22-slim

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install
# Force install of the specific binary and rebuild
RUN npm install @rollup/rollup-linux-arm64-gnu --save-optional
RUN npm rebuild

# Copy source
COPY . .

# Expose Vite default port
EXPOSE 5173

# Run dev server
CMD ["npm", "run", "dev", "--", "--host"]
