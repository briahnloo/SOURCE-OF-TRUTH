FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Build Next.js app
RUN npm run build

EXPOSE 3000

# Start Next.js in production mode
CMD ["npm", "start"]
