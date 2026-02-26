# Day 6: Storage Quota Display UI

**Goal**: Display storage usage and quota for all cloud providers
**Estimated Time**: 4-6 hours
**Priority**: MEDIUM - Transparency for users

---

## Morning Session (2-3 hours)

### Task 6.1: Create storage stats component (60 min)

**File: `frontend/components/StorageStats.tsx`**
```typescript
'use client';

import { useEffect, useState } from 'react';
import { Cloud, HardDrive } from 'lucide-react';

interface StorageProvider {
  provider: string;
  total_size_bytes: number;
  total_size_gb: number;
  file_count: number;
  available_bytes: number;
  available_gb: number;
  used_percentage: number;
  is_full: boolean;
  last_updated: string;
}

interface StorageStatsResponse {
  providers: StorageProvider[];
  total_used_gb: number;
  total_available_gb: number;
  overall_used_percentage: number;
}

export function StorageStats() {
  const [stats, setStats] = useState<StorageStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
    // Refresh every minute
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/storage/stats`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch storage stats');
      }

      const data = await response.json();
      setStats(data);
      setError(null);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'gcs':
        return '☁️';
      case 'azure':
        return '🔷';
      case 's3':
        return '📦';
      default:
        return '💾';
    }
  };

  const getProviderName = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'gcs':
        return 'Google Cloud';
      case 'azure':
        return 'Azure Blob';
      case 's3':
        return 'AWS S3';
      default:
        return provider;
    }
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-12 bg-gray-200 rounded"></div>
            <div className="h-12 bg-gray-200 rounded"></div>
            <div className="h-12 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-600">
          <p className="font-medium">Failed to load storage stats</p>
          <p className="text-sm mt-1">{error}</p>
          <button
            onClick={fetchStats}
            className="mt-3 text-sm text-blue-600 hover:underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <HardDrive size={24} />
          Storage Usage
        </h2>
        <button
          onClick={fetchStats}
          className="text-sm text-blue-600 hover:underline"
        >
          Refresh
        </button>
      </div>

      {/* Overall stats */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600">Total Usage</span>
          <span className="text-sm font-medium">
            {stats.total_used_gb.toFixed(2)} GB / {(stats.total_used_gb + stats.total_available_gb).toFixed(2)} GB
          </span>
        </div>
        <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getProgressColor(stats.overall_used_percentage)}`}
            style={{ width: `${stats.overall_used_percentage}%` }}
          ></div>
        </div>
        <div className="mt-2 text-right text-xs text-gray-500">
          {stats.overall_used_percentage.toFixed(1)}% used
        </div>
      </div>

      {/* Individual providers */}
      <div className="space-y-4">
        {stats.providers.map((provider) => (
          <div
            key={provider.provider}
            className={`p-4 rounded-lg border-2 transition-all ${
              provider.is_full
                ? 'border-red-300 bg-red-50'
                : 'border-gray-200 hover:border-blue-300'
            }`}
          >
            {/* Provider header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getProviderIcon(provider.provider)}</span>
                <div>
                  <h3 className="font-semibold">{getProviderName(provider.provider)}</h3>
                  <p className="text-xs text-gray-500">
                    {provider.file_count} files
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium">
                  {provider.total_size_gb.toFixed(2)} GB
                </div>
                <div className="text-xs text-gray-500">
                  {provider.available_gb.toFixed(2)} GB available
                </div>
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${getProgressColor(provider.used_percentage)}`}
                style={{ width: `${provider.used_percentage}%` }}
              ></div>
            </div>

            {/* Status */}
            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="text-gray-500">
                {provider.used_percentage.toFixed(1)}% used
              </span>
              {provider.is_full && (
                <span className="text-red-600 font-medium">
                  ⚠️ Storage Full
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Warning message if any provider is full */}
      {stats.providers.some(p => p.is_full) && (
        <div className="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800">
          <p className="font-medium">Storage Alert</p>
          <p className="text-sm mt-1">
            One or more storage providers have reached capacity. New downloads will use available providers.
          </p>
        </div>
      )}
    </div>
  );
}
```

---

### Task 6.2: Add storage stats to home page (30 min)

**File: `frontend/app/page.tsx`** (Add storage stats)
```typescript
import { StorageStats } from '@/components/StorageStats';

export default function Home() {
  // ... existing code ...

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main content - 2/3 width on large screens */}
        <div className="lg:col-span-2">
          <h1 className="text-4xl font-bold mb-8">YouTube Shorts Downloader</h1>

          {/* Download form and results */}
          {/* ... existing download UI ... */}
        </div>

        {/* Sidebar - 1/3 width on large screens */}
        <div className="lg:col-span-1">
          <StorageStats />
        </div>
      </div>
    </div>
  );
}
```

---

### Task 6.3: Create compact storage indicator (45 min)

**File: `frontend/components/StorageIndicator.tsx`**
```typescript
'use client';

import { useEffect, useState } from 'react';

interface StorageIndicatorProps {
  compact?: boolean;
}

export function StorageIndicator({ compact = false }: StorageIndicatorProps) {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/storage/stats`
      );
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch storage stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !stats) return null;

  const getStatusColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600';
    if (percentage >= 70) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-600">Storage:</span>
        <span className={`font-medium ${getStatusColor(stats.overall_used_percentage)}`}>
          {stats.total_used_gb.toFixed(1)} GB / {(stats.total_used_gb + stats.total_available_gb).toFixed(1)} GB
        </span>
        <span className="text-gray-400">
          ({stats.overall_used_percentage.toFixed(0)}%)
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium">Total Storage</span>
        <span className="text-sm text-gray-600">
          {stats.total_used_gb.toFixed(2)} GB used
        </span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all ${
            stats.overall_used_percentage >= 90
              ? 'bg-red-500'
              : stats.overall_used_percentage >= 70
              ? 'bg-yellow-500'
              : 'bg-green-500'
          }`}
          style={{ width: `${stats.overall_used_percentage}%` }}
        ></div>
      </div>
    </div>
  );
}
```

---

## Afternoon Session (2-3 hours)

### Task 6.4: Update storage stats API response (45 min)

**File: `backend-python/app/routes/storage_routes.py`** (Update response)
```python
from fastapi import APIRouter
from app.services.storage_tracker import storage_tracker
from app.models.storage_stats import AllStorageStatsResponse
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/storage", tags=["storage"])


class EnhancedStorageStatsResponse(BaseModel):
    """Enhanced storage statistics with totals"""
    providers: List[dict]
    total_used_gb: float
    total_available_gb: float
    overall_used_percentage: float


@router.get("/stats", response_model=EnhancedStorageStatsResponse)
async def get_storage_stats():
    """Get enhanced storage usage statistics for all cloud providers"""
    stats = await storage_tracker.get_all_stats()

    # Calculate totals
    total_used_bytes = sum(p['total_size_bytes'] for p in stats['providers'])
    total_available_bytes = sum(p['available_bytes'] for p in stats['providers'])
    total_capacity_bytes = total_used_bytes + total_available_bytes

    total_used_gb = total_used_bytes / (1024 ** 3)
    total_available_gb = total_available_bytes / (1024 ** 3)
    overall_used_percentage = (total_used_bytes / total_capacity_bytes * 100) if total_capacity_bytes > 0 else 0

    return EnhancedStorageStatsResponse(
        providers=stats['providers'],
        total_used_gb=total_used_gb,
        total_available_gb=total_available_gb,
        overall_used_percentage=overall_used_percentage
    )
```

---

### Task 6.5: Add storage stats to navigation (30 min)

**File: `frontend/components/Navigation.tsx`** (Add storage indicator)
```typescript
import { StorageIndicator } from './StorageIndicator';

export function Navigation() {
  // ... existing code ...

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Left side - logo and links */}
          <div className="flex items-center gap-8">
            <Link href="/" className="text-xl font-bold text-blue-600">
              YTD Downloader
            </Link>

            <div className="flex gap-4">
              {links.map((link) => (
                <Link key={link.href} href={link.href} /* ... */>
                  {link.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Right side - storage indicator */}
          <div>
            <StorageIndicator compact />
          </div>
        </div>
      </div>
    </nav>
  );
}
```

---

### Task 6.6: Create storage details modal (60 min)

**File: `frontend/components/StorageDetailsModal.tsx`**
```typescript
'use client';

import { X } from 'lucide-react';
import { StorageStats } from './StorageStats';

interface StorageDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function StorageDetailsModal({ isOpen, onClose }: StorageDetailsModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <h2 className="text-2xl font-bold">Storage Details</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            <StorageStats />
          </div>
        </div>
      </div>
    </div>
  );
}
```

**Update `StorageIndicator` to open modal:**
```typescript
import { useState } from 'react';
import { StorageDetailsModal } from './StorageDetailsModal';

export function StorageIndicator({ compact = false }: StorageIndicatorProps) {
  const [showModal, setShowModal] = useState(false);
  // ... existing code ...

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 text-sm hover:text-blue-600 transition-colors"
      >
        {/* ... existing indicator content ... */}
      </button>

      <StorageDetailsModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
      />
    </>
  );
}
```

---

### Task 6.7: Add storage alerts (45 min)

**File: `frontend/components/StorageAlert.tsx`**
```typescript
'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

export function StorageAlert() {
  const [show, setShow] = useState(false);
  const [fullProviders, setFullProviders] = useState<string[]>([]);

  useEffect(() => {
    checkStorage();
    const interval = setInterval(checkStorage, 60000);
    return () => clearInterval(interval);
  }, []);

  const checkStorage = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/storage/stats`
      );
      const data = await response.json();

      const full = data.providers
        .filter((p: any) => p.is_full)
        .map((p: any) => p.provider);

      setFullProviders(full);
      setShow(full.length > 0);

    } catch (error) {
      console.error('Failed to check storage:', error);
    }
  };

  if (!show) return null;

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
      <div className="flex items-start">
        <AlertTriangle className="text-yellow-600 flex-shrink-0 mt-0.5" size={20} />
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-yellow-800">
            Storage Capacity Warning
          </h3>
          <p className="mt-1 text-sm text-yellow-700">
            {fullProviders.length === 1
              ? `${fullProviders[0].toUpperCase()} storage is at capacity.`
              : `${fullProviders.join(', ').toUpperCase()} storage providers are at capacity.`}
            {' '}New downloads will use available providers.
          </p>
        </div>
        <button
          onClick={() => setShow(false)}
          className="ml-3 flex-shrink-0 text-yellow-600 hover:text-yellow-800"
        >
          <X size={20} />
        </button>
      </div>
    </div>
  );
}
```

Add to home page:
```typescript
import { StorageAlert } from '@/components/StorageAlert';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      <StorageAlert />
      {/* ... rest of page ... */}
    </div>
  );
}
```

---

## End of Day Checklist

- [ ] StorageStats component created
- [ ] Storage stats added to home page
- [ ] Compact storage indicator created
- [ ] Storage stats API response enhanced
- [ ] Storage indicator added to navigation
- [ ] Storage details modal implemented
- [ ] Storage alert component created
- [ ] All components tested
- [ ] UI responsive on mobile
- [ ] Code committed to git

**Git Commit**:
```bash
git add .
git commit -m "Day 6: Add storage quota display UI

- Created comprehensive StorageStats component
- Added storage sidebar to home page
- Implemented compact storage indicator
- Enhanced storage stats API with totals
- Added storage indicator to navigation
- Created storage details modal
- Implemented storage capacity alerts
- Responsive design for all screen sizes"
```

---

## Success Metrics

✅ **Complete** if:
- Storage stats visible on home page
- Navigation shows storage indicator
- Modal shows detailed stats
- Alerts appear when storage full
- Real-time updates working
- Mobile responsive

## Summary

You now have complete implementation plans for 6 days of work:

- **Day 1**: Testing infrastructure and unit tests
- **Day 2**: Structured error handling with custom exceptions
- **Day 3**: Prometheus metrics and monitoring
- **Day 4**: WebSocket for real-time progress
- **Day 5**: Download history UI with pagination
- **Day 6**: Storage quota display

Each day builds on the previous, creating a production-ready application with:
- ✅ Comprehensive testing
- ✅ Robust error handling
- ✅ Full observability
- ✅ Real-time updates
- ✅ Complete user features
- ✅ Transparency and visibility

Start with Day 1 and work through each plan systematically!
