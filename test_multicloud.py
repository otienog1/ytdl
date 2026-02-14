"""
Test script for multi-cloud storage implementation
Tests GCS, Azure, S3 credentials and permissions
"""
import asyncio
import os
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.settings import settings
from app.config.multi_storage import multi_storage
from app.services.storage_service import storage_service
from app.services.storage_tracker import storage_tracker
from app.services.email_service import email_service
from app.utils.logger import logger


async def test_environment_variables():
    """Test 1: Verify environment variables are loaded"""
    print("\n" + "="*60)
    print("TEST 1: Environment Variables")
    print("="*60)

    print(f"\n✓ GCP Project ID: {settings.GCP_PROJECT_ID}")
    print(f"✓ GCS Bucket: {settings.GCP_BUCKET_NAME}")

    if settings.AZURE_STORAGE_CONNECTION_STRING:
        print(f"✓ Azure Connection String: {settings.AZURE_STORAGE_CONNECTION_STRING[:30]}...")
        print(f"✓ Azure Container: {settings.AZURE_CONTAINER_NAME}")
    else:
        print("✗ Azure not configured")

    if settings.AWS_ACCESS_KEY_ID:
        print(f"✓ AWS Access Key ID: {settings.AWS_ACCESS_KEY_ID[:10]}...")
        print(f"✓ AWS Bucket: {settings.AWS_S3_BUCKET_NAME}")
        print(f"✓ AWS Region: {settings.AWS_REGION}")
    else:
        print("✗ AWS not configured")

    if settings.MAILGUN_SMTP_USER:
        print(f"✓ Mailgun SMTP User: {settings.MAILGUN_SMTP_USER}")
        print(f"✓ Alert Email From: {settings.ALERT_EMAIL_FROM}")
        print(f"✓ Alert Email To: {settings.ALERT_EMAIL_TO}")
    else:
        print("✗ Mailgun not configured")

    print(f"\n✓ Storage Limit: {settings.STORAGE_LIMIT_BYTES / (1024**3):.2f} GB")

    return True


async def test_provider_initialization():
    """Test 2: Test cloud provider initialization"""
    print("\n" + "="*60)
    print("TEST 2: Cloud Provider Initialization")
    print("="*60)

    available_providers = multi_storage.get_available_providers()
    print(f"\n✓ Available providers: {', '.join(available_providers)}")

    if not available_providers:
        print("✗ ERROR: No providers initialized!")
        return False

    # Test GCS
    if "gcs" in available_providers:
        try:
            gcs_client = multi_storage.get_gcs_client()
            bucket = multi_storage.get_gcs_bucket()
            print(f"✓ GCS initialized - Bucket: {bucket.name}")
        except Exception as e:
            print(f"✗ GCS initialization failed: {e}")
            return False

    # Test Azure
    if "azure" in available_providers:
        try:
            azure_client = multi_storage.get_azure_client()
            print(f"✓ Azure Blob Storage initialized")
        except Exception as e:
            print(f"✗ Azure initialization failed: {e}")
            return False

    # Test S3
    if "s3" in available_providers:
        try:
            s3_client = multi_storage.get_s3_client()
            print(f"✓ AWS S3 initialized")
        except Exception as e:
            print(f"✗ S3 initialization failed: {e}")
            return False

    return True


async def test_storage_permissions():
    """Test 3: Test upload, list, and delete permissions for each provider"""
    print("\n" + "="*60)
    print("TEST 3: Storage Permissions (Upload/List/Delete)")
    print("="*60)

    # Create a test file
    test_file_path = "test_multicloud_upload.txt"
    test_content = "This is a test file for multi-cloud storage verification"

    with open(test_file_path, "w") as f:
        f.write(test_content)

    print(f"\n✓ Created test file: {test_file_path}")

    available_providers = multi_storage.get_available_providers()

    for provider in available_providers:
        print(f"\n--- Testing {provider.upper()} ---")

        try:
            # Test upload
            print(f"  → Uploading test file to {provider}...")
            if provider == "gcs":
                url = await storage_service._upload_to_gcs(test_file_path, f"test_{provider}.txt")
            elif provider == "azure":
                url = await storage_service._upload_to_azure(test_file_path, f"test_{provider}.txt")
            elif provider == "s3":
                url = await storage_service._upload_to_s3(test_file_path, f"test_{provider}.txt")

            print(f"  ✓ Upload successful")
            print(f"  ✓ Signed URL generated: {url[:60]}...")

            # Test list/check existence
            print(f"  → Checking file exists in {provider}...")
            file_size = await storage_service._get_file_size(f"test_{provider}.txt", provider)
            print(f"  ✓ File exists, size: {file_size} bytes")

            # Test delete
            print(f"  → Deleting test file from {provider}...")
            if provider == "gcs":
                await storage_service._delete_from_gcs(f"test_{provider}.txt")
            elif provider == "azure":
                await storage_service._delete_from_azure(f"test_{provider}.txt")
            elif provider == "s3":
                await storage_service._delete_from_s3(f"test_{provider}.txt")

            print(f"  ✓ Delete successful")
            print(f"  ✓ {provider.upper()} permissions verified!")

        except Exception as e:
            print(f"  ✗ {provider.upper()} test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Cleanup local test file
    os.remove(test_file_path)
    print(f"\n✓ Cleaned up local test file")

    return True


async def test_storage_tracking():
    """Test 4: Test storage tracking system"""
    print("\n" + "="*60)
    print("TEST 4: Storage Tracking System")
    print("="*60)

    try:
        # Initialize stats for all providers
        available_providers = multi_storage.get_available_providers()

        for provider in available_providers:
            await storage_tracker.initialize_provider_stats(provider)
            print(f"✓ Initialized stats for {provider}")

        # Get stats for each provider
        print("\nProvider Statistics:")
        for provider in available_providers:
            stats = await storage_tracker.get_provider_stats(provider)
            if stats:
                print(f"\n  {provider.upper()}:")
                print(f"    - Total Size: {stats.total_size_gb:.2f} GB")
                print(f"    - File Count: {stats.file_count}")
                print(f"    - Available: {stats.available_gb:.2f} GB")
                print(f"    - Used: {stats.used_percentage:.1f}%")
                print(f"    - Is Full: {stats.is_full}")

        # Test get_available_providers_under_limit
        available_under_limit = await storage_tracker.get_available_providers_under_limit()
        print(f"\n✓ Providers under limit: {', '.join(available_under_limit)}")

        return True

    except Exception as e:
        print(f"✗ Storage tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_email_service():
    """Test 5: Test email notification service"""
    print("\n" + "="*60)
    print("TEST 5: Email Notification Service")
    print("="*60)

    if not settings.MAILGUN_SMTP_USER:
        print("✗ Mailgun not configured, skipping email test")
        return True

    try:
        print("\nSending test email...")
        print(f"  From: {settings.ALERT_EMAIL_FROM}")
        print(f"  To: {settings.ALERT_EMAIL_TO}")

        # Send test alert
        await email_service.send_storage_alert(
            provider="gcs",
            total_size_gb=5.02,
            limit_gb=5.0
        )

        print("✓ Test email sent successfully!")
        print("  → Check your inbox to verify receipt")

        return True

    except Exception as e:
        print(f"✗ Email test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_workflow():
    """Test 6: Test complete upload/track/delete workflow"""
    print("\n" + "="*60)
    print("TEST 6: Complete Upload → Track → Delete Workflow")
    print("="*60)

    # Create a test file
    test_file_path = "test_workflow.txt"
    test_content = "Testing complete workflow" * 1000  # ~25KB

    with open(test_file_path, "w") as f:
        f.write(test_content)

    file_size = os.path.getsize(test_file_path)
    print(f"\n✓ Created test file: {test_file_path} ({file_size} bytes)")

    try:
        # Test upload (should select random provider)
        print("\n→ Testing upload with random provider selection...")
        url, provider, returned_size = await storage_service.upload_file(test_file_path, "workflow_test.txt")

        print(f"✓ File uploaded to {provider}")
        print(f"✓ File size: {returned_size} bytes")
        print(f"✓ URL generated: {url[:60]}...")

        # Extract the actual filename from URL
        from urllib.parse import urlparse, unquote
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        actual_filename = unquote(path_parts[-1]) if path_parts else "workflow_test.txt"

        # Verify tracking was updated
        print(f"\n→ Verifying storage tracking updated...")
        stats = await storage_tracker.get_provider_stats(provider)
        print(f"✓ {provider} current usage: {stats.total_size_gb:.4f} GB ({stats.file_count} files)")

        # Test deletion using actual filename
        print(f"\n→ Testing file deletion...")
        await storage_service.delete_file(actual_filename, provider)
        print(f"✓ File deleted from {provider}")

        # Verify tracking was updated after deletion
        stats_after = await storage_tracker.get_provider_stats(provider)
        print(f"✓ {provider} usage after delete: {stats_after.total_size_gb:.4f} GB ({stats_after.file_count} files)")

        # Cleanup local file
        os.remove(test_file_path)
        print(f"\n✓ Complete workflow test successful!")

        return True

    except Exception as e:
        print(f"✗ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()

        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MULTI-CLOUD STORAGE TEST SUITE")
    print("="*60)

    results = []

    # Test 1: Environment Variables
    results.append(("Environment Variables", await test_environment_variables()))

    # Test 2: Provider Initialization
    results.append(("Provider Initialization", await test_provider_initialization()))

    # Test 3: Storage Permissions
    results.append(("Storage Permissions", await test_storage_permissions()))

    # Test 4: Storage Tracking
    results.append(("Storage Tracking", await test_storage_tracking()))

    # Test 5: Email Service
    results.append(("Email Service", await test_email_service()))

    # Test 6: Full Workflow
    results.append(("Full Workflow", await test_full_workflow()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<40} {status}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print("\n" + "="*60)
    print(f"RESULTS: {total_passed}/{total_tests} tests passed")
    print("="*60)

    if total_passed == total_tests:
        print("\n🎉 All tests passed! Multi-cloud storage is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
