import { Router } from 'express';
import downloadController from '../controllers/downloadController';

const router = Router();

// GET /api/history - Get download history
router.get('/', downloadController.getDownloadHistory);

export default router;
