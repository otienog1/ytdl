# Day 5: Download History UI

**Goal**: Create download history page with pagination and filters
**Estimated Time**: 6-8 hours
**Priority**: MEDIUM - Improves user experience

---

## Morning Session (3-4 hours)

### Task 5.1: Create history page route (30 min)

**File: `frontend/app/history/page.tsx`**
```typescript
'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { HistoryList } from '@/components/HistoryList';
import { HistoryFilters } from '@/components/HistoryFilters';
import { Pagination } from '@/components/Pagination';

interface Download {
  jobId: string;
  url: string;
  status: 'completed' | 'failed' | 'queued' | 'processing';
  progress: number;
  videoInfo?: {
    id: string;
    title: string;
    thumbnail: string;
    duration: number;
    quality?: string;
  };
  downloadUrl?: string;
  storageProvider?: string;
  fileSize?: number;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

interface HistoryResponse {
  downloads: Download[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export default function HistoryPage() {
  const searchParams = useSearchParams();
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const page = parseInt(searchParams.get('page') || '1');
  const limit = parseInt(searchParams.get('limit') || '20');
  const status = searchParams.get('status') || '';

  useEffect(() => {
    fetchHistory();
  }, [page, limit, status]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        ...(status && { status })
      });

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/history?${params}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch history');
      }

      const data = await response.json();
      setHistory(data);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">Download History</h1>

      {/* Filters */}
      <HistoryFilters
        currentStatus={status}
        onFilterChange={(newStatus) => {
          const params = new URLSearchParams(window.location.search);
          if (newStatus) {
            params.set('status', newStatus);
          } else {
            params.delete('status');
          }
          params.set('page', '1'); // Reset to page 1
          window.location.search = params.toString();
        }}
      />

      {/* Loading state */}
      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading history...</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">
          {error}
        </div>
      )}

      {/* History list */}
      {!loading && !error && history && (
        <>
          {history.downloads.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p className="text-lg">No downloads found</p>
              <a href="/" className="text-blue-600 hover:underline mt-2 inline-block">
                Start downloading
              </a>
            </div>
          ) : (
            <>
              <HistoryList downloads={history.downloads} onRefresh={fetchHistory} />

              {/* Pagination */}
              <Pagination
                currentPage={history.page}
                totalPages={history.totalPages}
                total={history.total}
                limit={history.limit}
              />
            </>
          )}
        </>
      )}
    </div>
  );
}
```

---

### Task 5.2: Create history list component (60 min)

**File: `frontend/components/HistoryList.tsx`**
```typescript
import { formatDistanceToNow } from 'date-fns';
import { HistoryItem } from './HistoryItem';

interface Download {
  jobId: string;
  url: string;
  status: 'completed' | 'failed' | 'queued' | 'processing';
  videoInfo?: {
    title: string;
    thumbnail: string;
    duration: number;
    quality?: string;
  };
  downloadUrl?: string;
  storageProvider?: string;
  fileSize?: number;
  error?: string;
  createdAt: string;
}

interface HistoryListProps {
  downloads: Download[];
  onRefresh: () => void;
}

export function HistoryList({ downloads, onRefresh }: HistoryListProps) {
  return (
    <div className="space-y-4">
      {downloads.map((download) => (
        <HistoryItem
          key={download.jobId}
          download={download}
          onRefresh={onRefresh}
        />
      ))}
    </div>
  );
}
```

**File: `frontend/components/HistoryItem.tsx`**
```typescript
import { formatDistanceToNow } from 'date-fns';
import { Download, Trash2, RefreshCw } from 'lucide-react';
import { useState } from 'react';

interface HistoryItemProps {
  download: {
    jobId: string;
    url: string;
    status: 'completed' | 'failed' | 'queued' | 'processing';
    videoInfo?: {
      title: string;
      thumbnail: string;
      duration: number;
      quality?: string;
    };
    downloadUrl?: string;
    storageProvider?: string;
    fileSize?: number;
    error?: string;
    createdAt: string;
  };
  onRefresh: () => void;
}

export function HistoryItem({ download, onRefresh }: HistoryItemProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Delete this download from history?')) return;

    try {
      setIsDeleting(true);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/download/${download.jobId}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        onRefresh();
      }

    } catch (error) {
      console.error('Error deleting:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        {/* Thumbnail */}
        {download.videoInfo?.thumbnail && (
          <img
            src={download.videoInfo.thumbnail}
            alt={download.videoInfo.title}
            className="w-32 h-18 object-cover rounded"
          />
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="font-semibold text-lg truncate">
            {download.videoInfo?.title || 'Untitled'}
          </h3>

          {/* Metadata */}
          <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(download.status)}`}>
              {download.status}
            </span>

            {download.storageProvider && (
              <span className="capitalize">{download.storageProvider}</span>
            )}

            {download.videoInfo?.quality && (
              <span>{download.videoInfo.quality}</span>
            )}

            <span>{formatFileSize(download.fileSize)}</span>

            <span className="text-gray-400">
              {formatDistanceToNow(new Date(download.createdAt), { addSuffix: true })}
            </span>
          </div>

          {/* Error message */}
          {download.error && (
            <div className="mt-2 text-sm text-red-600">
              {download.error}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {download.status === 'completed' && download.downloadUrl && (
            <a
              href={download.downloadUrl}
              download
              className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
              title="Download"
            >
              <Download size={20} />
            </a>
          )}

          {download.status === 'failed' && (
            <button
              onClick={() => window.location.href = `/?url=${encodeURIComponent(download.url)}`}
              className="p-2 text-green-600 hover:bg-green-50 rounded transition-colors"
              title="Retry"
            >
              <RefreshCw size={20} />
            </button>
          )}

          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50"
            title="Delete"
          >
            <Trash2 size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

### Task 5.3: Create filter component (45 min)

**File: `frontend/components/HistoryFilters.tsx`**
```typescript
interface HistoryFiltersProps {
  currentStatus: string;
  onFilterChange: (status: string) => void;
}

export function HistoryFilters({ currentStatus, onFilterChange }: HistoryFiltersProps) {
  const statuses = [
    { value: '', label: 'All' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
    { value: 'processing', label: 'Processing' },
    { value: 'queued', label: 'Queued' }
  ];

  return (
    <div className="mb-6 flex gap-2">
      <label className="font-medium text-gray-700 flex items-center">
        Filter by status:
      </label>

      <div className="flex gap-2">
        {statuses.map((status) => (
          <button
            key={status.value}
            onClick={() => onFilterChange(status.value)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              currentStatus === status.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status.label}
          </button>
        ))}
      </div>
    </div>
  );
}
```

---

## Afternoon Session (3-4 hours)

### Task 5.4: Create pagination component (60 min)

**File: `frontend/components/Pagination.tsx`**
```typescript
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  total: number;
  limit: number;
}

export function Pagination({ currentPage, totalPages, total, limit }: PaginationProps) {
  const changePage = (page: number) => {
    const params = new URLSearchParams(window.location.search);
    params.set('page', page.toString());
    window.location.search = params.toString();
  };

  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const showPages = 5;

    if (totalPages <= showPages) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    // Always show first page
    pages.push(1);

    if (currentPage > 3) {
      pages.push('...');
    }

    // Show pages around current
    for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
      pages.push(i);
    }

    if (currentPage < totalPages - 2) {
      pages.push('...');
    }

    // Always show last page
    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  };

  const startItem = (currentPage - 1) * limit + 1;
  const endItem = Math.min(currentPage * limit, total);

  return (
    <div className="mt-8 flex items-center justify-between">
      {/* Results info */}
      <div className="text-sm text-gray-600">
        Showing {startItem} to {endItem} of {total} results
      </div>

      {/* Page navigation */}
      <div className="flex items-center gap-2">
        {/* Previous button */}
        <button
          onClick={() => changePage(currentPage - 1)}
          disabled={currentPage === 1}
          className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeft size={20} />
        </button>

        {/* Page numbers */}
        {getPageNumbers().map((page, index) => (
          typeof page === 'number' ? (
            <button
              key={index}
              onClick={() => changePage(page)}
              className={`px-4 py-2 rounded ${
                currentPage === page
                  ? 'bg-blue-600 text-white'
                  : 'hover:bg-gray-100'
              }`}
            >
              {page}
            </button>
          ) : (
            <span key={index} className="px-2 text-gray-400">
              {page}
            </span>
          )
        ))}

        {/* Next button */}
        <button
          onClick={() => changePage(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronRight size={20} />
        </button>
      </div>
    </div>
  );
}
```

---

### Task 5.5: Update backend history endpoint (60 min)

**File: `backend-python/app/routes/history.py`** (Update with pagination)
```python
from fastapi import APIRouter, Query
from typing import Optional
from app.config.database import get_database
from app.models.download import Download
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/history", tags=["history"])


class HistoryResponse(BaseModel):
    downloads: List[Download]
    total: int
    page: int
    limit: int
    totalPages: int


@router.get("", response_model=HistoryResponse)
async def get_download_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    """Get paginated download history with optional status filter"""
    try:
        db = get_database()

        # Build filter
        query_filter = {}
        if status:
            query_filter["status"] = status

        # Get total count
        total = await db.downloads.count_documents(query_filter)

        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total + limit - 1) // limit

        # Get downloads
        cursor = db.downloads.find(query_filter) \
            .sort('createdAt', -1) \
            .skip(skip) \
            .limit(limit)

        downloads = await cursor.to_list(length=limit)

        return HistoryResponse(
            downloads=[Download(**download) for download in downloads],
            total=total,
            page=page,
            limit=limit,
            totalPages=total_pages
        )

    except Exception as e:
        logger.error(f"Error fetching download history: {e}")
        raise


@router.delete("/{job_id}")
async def delete_download(job_id: str):
    """Delete download from history"""
    try:
        db = get_database()

        result = await db.downloads.delete_one({"jobId": job_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Download not found")

        return {"success": True, "message": "Download deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting download: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete download")
```

---

### Task 5.6: Add navigation to history page (30 min)

**File: `frontend/components/Navigation.tsx`**
```typescript
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Navigation() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Download' },
    { href: '/history', label: 'History' },
    { href: '/about', label: 'About' }
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-xl font-bold text-blue-600">
              YTD Downloader
            </Link>

            <div className="flex gap-4">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-2 rounded transition-colors ${
                    pathname === link.href
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
```

**File: `frontend/app/layout.tsx`** (Add navigation)
```typescript
import { Navigation } from '@/components/Navigation';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Navigation />
        {children}
      </body>
    </html>
  );
}
```

---

### Task 5.7: Install date-fns for date formatting (15 min)

```bash
cd frontend
npm install date-fns lucide-react
```

---

### Task 5.8: Test history page (45 min)

**Test Plan:**

1. **Basic Functionality**
   - Navigate to /history
   - Verify downloads are displayed
   - Check pagination works
   - Test filters

2. **Pagination Tests**
   - Click next/previous buttons
   - Click page numbers
   - Verify correct items displayed
   - Test with different page sizes

3. **Filter Tests**
   - Filter by "Completed"
   - Filter by "Failed"
   - Filter by "All"
   - Verify counts update

4. **Actions Tests**
   - Download completed video
   - Retry failed download
   - Delete download from history

5. **Edge Cases**
   - Empty history
   - Single item
   - Many items (100+)
   - Long video titles

---

## End of Day Checklist

- [ ] History page route created
- [ ] History list component created
- [ ] History item component with actions
- [ ] Filter component working
- [ ] Pagination component implemented
- [ ] Backend pagination endpoint updated
- [ ] Delete endpoint working
- [ ] Navigation added to layout
- [ ] date-fns installed
- [ ] All functionality tested
- [ ] Code committed to git

**Git Commit**:
```bash
git add .
git commit -m "Day 5: Add download history UI

- Created history page with pagination
- Implemented history list and item components
- Added status filters
- Created pagination component
- Updated backend with pagination support
- Added delete from history functionality
- Implemented retry for failed downloads
- Added navigation component
- Integrated date formatting with date-fns"
```

---

## Success Metrics

✅ **Complete** if:
- History page displays downloads
- Pagination working correctly
- Filters functioning
- Delete and retry actions work
- Navigation visible across app

## Tomorrow Preview

**Day 6**: Display storage quota UI
- Show storage usage per provider
- Create storage stats component
- Add visual progress bars
- Display remaining capacity
- Integrate with existing /api/storage/stats endpoint
