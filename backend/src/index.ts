// Load environment variables FIRST, before any other imports
import dotenv from 'dotenv';
dotenv.config();

import express, { Application } from 'express';
import helmet from 'helmet';
import connectDatabase from './config/database';
import corsMiddleware from './middleware/cors';
import { errorHandler, notFoundHandler } from './middleware/errorHandler';
import { apiLimiter } from './middleware/rateLimiter';
import logger from './utils/logger';
import storageService from './services/storageService';

// Import routes
import downloadRoutes from './routes/download';
import statusRoutes from './routes/status';
import historyRoutes from './routes/history';

const app: Application = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(corsMiddleware);
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(apiLimiter);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API Routes
app.use('/api/download', downloadRoutes);
app.use('/api/status', statusRoutes);
app.use('/api/history', historyRoutes);

// Error handling
app.use(notFoundHandler);
app.use(errorHandler);

// Initialize database and start server
const startServer = async () => {
  try {
    // Connect to MongoDB
    await connectDatabase();

    // Start cleanup job for old files (runs every hour)
    const fileExpiryHours = parseInt(process.env.FILE_EXPIRY_HOURS || '24');
    setInterval(async () => {
      logger.info('Running cleanup job for old files...');
      await storageService.cleanupOldFiles(fileExpiryHours);
    }, 60 * 60 * 1000); // Run every hour

    // Start Express server
    app.listen(PORT, () => {
      logger.info(`Server is running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
};

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', error);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM signal received: closing HTTP server');
  process.exit(0);
});

startServer();

export default app;
