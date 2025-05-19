FROM node:18-alpine

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
COPY package-lock.json ./
RUN npm install
RUN npm install next

# Copy the rest of the application
COPY . .

# Set environment for NextJS
ENV PORT 3000
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED 1

# Expose the port
EXPOSE 3000

# Start the development server
CMD ["npx", "next", "dev", "-p", "3000", "--hostname", "0.0.0.0"]