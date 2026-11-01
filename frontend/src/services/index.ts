import type { JobBoardService } from './job-board-service';
import { HttpJobBoardService } from './http-job-board-service';
import { MockJobBoardService } from './mock-job-board-service';

export const jobBoardService: JobBoardService = import.meta.env.VITE_DATA_MODE === 'mock'
  ? new MockJobBoardService(typeof window !== 'undefined' ? window.localStorage : undefined)
  : new HttpJobBoardService();
