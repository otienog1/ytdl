import { Router } from 'express';
import downloadController from '../controllers/downloadController';
import { downloadLimiter } from '../middleware/rateLimiter';

const router = Router();

// POST /api/download - Initiate a new download
router.post('/', downloadLimiter, downloadController.initiateDownload);

export default router;
