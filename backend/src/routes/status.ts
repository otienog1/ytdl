import { Router } from 'express';
import downloadController from '../controllers/downloadController';

const router = Router();

// GET /api/status/:jobId - Get download status
router.get('/:jobId', downloadController.getDownloadStatus);

export default router;
