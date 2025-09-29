# """
# Django management command to clean up orphaned files and old data
# Usage: python manage.py cleanup_files [--dry-run] [--days=30]
# """

# import os
# from datetime import timedelta
# from django.core.management.base import BaseCommand, CommandError
# from django.utils import timezone
# from django.conf import settings
# from django.core.files.storage import default_storage
# from django.db import transaction
# from Lexibots_app.models import LegalDocument, ChatSession, ChatMessage, AnalyticsEvent


# class Command(BaseCommand):
#     help = 'Clean up orphaned files and old data from LexiBots'
    
#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--dry-run',
#             action='store_true',
#             help='Show what would be deleted without actually deleting',
#         )
#         parser.add_argument(
#             '--days',
#             type=int,
#             default=30,
#             help='Delete data older than this many days (default: 30)',
#         )
#         parser.add_argument(
#             '--cleanup-files',
#             action='store_true',
#             help='Clean up orphaned files',
#         )
#         parser.add_argument(
#             '--cleanup-sessions',
#             action='store_true',
#             help='Clean up old chat sessions',
#         )
#         parser.add_argument(
#             '--cleanup-analytics',
#             action='store_true',
#             help='Clean up old analytics events',
#         )
#         parser.add_argument(
#             '--all',
#             action='store_true',
#             help='Run all cleanup operations',
#         )
    
#     def handle(self, *args, **options):
#         dry_run = options['dry_run']
#         days = options['days']
#         cutoff_date = timezone.now() - timedelta(days=days)
        
#         self.stdout.write(
#             self.style.SUCCESS(
#                 f"LexiBots Cleanup - {'DRY RUN' if dry_run else 'LIVE RUN'}"
#             )
#         )
#         self.stdout.write(f"Cutoff date: {cutoff_date}")
#         self.stdout.write("-" * 50)
        
#         # Determine what to clean up
#         cleanup_files = options['cleanup_files'] or options['all']
#         cleanup_sessions = options['cleanup_sessions'] or options['all']
#         cleanup_analytics = options['cleanup_analytics'] or options['all']
        
#         if not any([cleanup_files, cleanup_sessions, cleanup_analytics]):
#             self.stdout.write(
#                 self.style.WARNING(
#                     "No cleanup operations specified. Use --all or specific flags."
#                 )
#             )
#             return
        
#         try:
#             with transaction.atomic():
#                 if cleanup_files:
#                     self.cleanup_orphaned_files(dry_run)
                
#                 if cleanup_sessions:
#                     self.cleanup_old_sessions(cutoff_date, dry_run)
                
#                 if cleanup_analytics:
#                     self.cleanup_old_analytics(cutoff_date, dry_run)
                
#                 if dry_run:
#                     # Rollback transaction in dry run mode
#                     transaction.set_rollback(True)
#                     self.stdout.write(
#                         self.style.WARNING(
#                             "DRY RUN - No changes were made to the database"
#                         )
#                     )
#                 else:
#                     self.stdout.write(
#                         self.style.SUCCESS("Cleanup completed successfully!")
#                     )
                    
#         except Exception as e:
#             self.stdout.write(
#                 self.style.ERROR(f"Error during cleanup: {str(e)}")
#             )
#             raise CommandError(f"Cleanup failed: {str(e)}")
    
#     def cleanup_orphaned_files(self, dry_run=True):
#         """Clean up files that don't have corresponding database records"""
#         self.stdout.write("🗂️  Checking for orphaned files...")
        
#         try:
#             # Get all file paths from database
#             db_file_paths = set(
#                 LegalDocument.objects.exclude(file='').values_list('file', flat=True)
#             )
            
#             # Get all files in the media directory
#             media_root = settings.MEDIA_ROOT
#             legal_docs_path = os.path.join(media_root, 'legal_documents')
            
#             if not os.path.exists(legal_docs_path):
#                 self.stdout.write("   No legal documents directory found")
#                 return
            
#             orphaned_files = []
#             total_size = 0
            
#             for root, dirs, files in os.walk(legal_docs_path):
#                 for file in files:
#                     file_path = os.path.join(root, file)
#                     relative_path = os.path.relpath(file_path, media_root)
                    
#                     if relative_path not in db_file_paths:
#                         orphaned_files.append(file_path)
#                         try:
#                             file_size = os.path.getsize(file_path)
#                             total_size += file_size
#                         except OSError:
#                             pass
            
#             if orphaned_files:
#                 self.stdout.write(
#                     f"   Found {len(orphaned_files)} orphaned files "
#                     f"({self._format_bytes(total_size)})"
#                 )
                
#                 if not dry_run:
#                     deleted_count = 0
#                     for file_path in orphaned_files:
#                         try:
#                             os.remove(file_path)
#                             deleted_count += 1
#                         except OSError as e:
#                             self.stdout.write(
#                                 self.style.WARNING(
#                                     f"   Could not delete {file_path}: {e}"
#                                 )
#                             )
                    
#                     self.stdout.write(
#                         self.style.SUCCESS(f"   Deleted {deleted_count} orphaned files")
#                     )
#                 else:
#                     for file_path in orphaned_files[:10]:  # Show first 10
#                         self.stdout.write(f"   Would delete: {file_path}")
#                     if len(orphaned_files) > 10:
#                         self.stdout.write(f"   ... and {len(orphaned_files) - 10} more")
#             else:
#                 self.stdout.write("   No orphaned files found")
                
#         except Exception as e:
#             self.stdout.write(
#                 self.style.ERROR(f"   Error cleaning up files: {str(e)}")
#             )
    
#     def cleanup_old_sessions(self, cutoff_date, dry_run=True):
#         """Clean up old chat sessions and their messages"""
#         self.stdout.write("💬 Cleaning up old chat sessions...")
        
#         # Find inactive sessions older than cutoff date
#         old_sessions = ChatSession.objects.filter(
#             last_activity__lt=cutoff_date,
#             is_active=False
#         )
        
#         session_count = old_sessions.count()
        
#         if session_count > 0:
#             # Count related messages
#             message_count = ChatMessage.objects.filter(
#                 session__in=old_sessions
#             ).count()
            
#             self.stdout.write(
#                 f"   Found {session_count} old sessions with {message_count} messages"
#             )
            
#             if not dry_run:
#                 # Delete messages first (foreign key constraint)
#                 deleted_messages = ChatMessage.objects.filter(
#                     session__in=old_sessions
#                 ).delete()[0]
                
#                 # Delete sessions
#                 deleted_sessions = old_sessions.delete()[0]
                
#                 self.stdout.write(
#                     self.style.SUCCESS(
#                         f"   Deleted {deleted_sessions} sessions and {deleted_messages} messages"
#                     )
#                 )
#             else:
#                 self.stdout.write(
#                     f"   Would delete {session_count} sessions and {message_count} messages"
#                 )
#         else:
#             self.stdout.write("   No old sessions found")
    
#     def cleanup_old_analytics(self, cutoff_date, dry_run=True):
#         """Clean up old analytics events"""
#         self.stdout.write("📊 Cleaning up old analytics events...")
        
#         old_events = AnalyticsEvent.objects.filter(timestamp__lt=cutoff_date)
#         event_count = old_events.count()
        
#         if event_count > 0:
#             self.stdout.write(f"   Found {event_count} old analytics events")
            
#             if not dry_run:
#                 deleted_count = old_events.delete()[0]
#                 self.stdout.write(
#                     self.style.SUCCESS(f"   Deleted {deleted_count} analytics events")
#                 )
#             else:
#                 self.stdout.write(f"   Would delete {event_count} analytics events")
#         else:
#             self.stdout.write("   No old analytics events found")
    
#     def _format_bytes(self, bytes):
#         """Format bytes in human readable format"""
#         for unit in ['B', 'KB', 'MB', 'GB']:
#             if bytes < 1024.0:
#                 return f"{bytes:.1f} {unit}"
#             bytes /= 1024.0
#         return f"{bytes:.1f} TB"


# class Command(BaseCommand):
#     """Additional management commands for LexiBots"""
#     help = 'Additional LexiBots management utilities'
    
#     def add_arguments(self, parser):
#         subparsers = parser.add_subparsers(dest='action', help='Available actions')
        
#         # Stats command
#         stats_parser = subparsers.add_parser('stats', help='Show system statistics')
#         stats_parser.add_argument(
#             '--days',
#             type=int,
#             default=30,
#             help='Show stats for the last N days'
#         )
        
#         # Migrate sessions command
#         migrate_parser = subparsers.add_parser(
#             'migrate-sessions',
#             help='Migrate anonymous sessions to user accounts'
#         )
#         migrate_parser.add_argument(
#             '--user-id',
#             type=int,
#             required=True,
#             help='Target user ID for migration'
#         )
#         migrate_parser.add_argument(
#             '--session-keys',
#             nargs='+',
#             help='Session keys to migrate'
#         )
    
#     def handle(self, *args, **options):
#         action = options.get('action')
        
#         if action == 'stats':
#             self.show_stats(options['days'])
#         elif action == 'migrate-sessions':
#             self.migrate_sessions(options['user_id'], options.get('session_keys', []))
#         else:
#             self.print_help('manage.py', 'lexibots_utils')
    
#     def show_stats(self, days):
#         """Show system statistics"""
#         cutoff_date = timezone.now() - timedelta(days=days)
        
#         self.stdout.write(f"📈 LexiBots Statistics (Last {days} days)")
#         self.stdout.write("=" * 50)
        
#         # Document stats
#         total_docs = LegalDocument.objects.count()
#         recent_docs = LegalDocument.objects.filter(created_at__gte=cutoff_date).count()
#         active_docs = LegalDocument.objects.filter(is_active=True).count()
        
#         self.stdout.write(f"📄 Documents:")
#         self.stdout.write(f"   Total: {total_docs}")
#         self.stdout.write(f"   Recent: {recent_docs}")
#         self.stdout.write(f"   Active: {active_docs}")
        
#         # Session stats
#         total_sessions = ChatSession.objects.count()
#         recent_sessions = ChatSession.objects.filter(started_at__gte=cutoff_date).count()
#         active_sessions = ChatSession.objects.filter(is_active=True).count()
        
#         self.stdout.write(f"\n💬 Chat Sessions:")
#         self.stdout.write(f"   Total: {total_sessions}")
#         self.stdout.write(f"   Recent: {recent_sessions}")
#         self.stdout.write(f"   Active: {active_sessions}")
        
#         # Message stats
#         total_messages = ChatMessage.objects.count()
#         recent_messages = ChatMessage.objects.filter(timestamp__gte=cutoff_date).count()
        
#         self.stdout.write(f"\n✉️  Messages:")
#         self.stdout.write(f"   Total: {total_messages}")
#         self.stdout.write(f"   Recent: {recent_messages}")
        
#         # User stats
#         registered_users = UserPreference.objects.filter(user__isnull=False).count()
#         anonymous_sessions = UserPreference.objects.filter(user__isnull=True).count()
        
#         self.stdout.write(f"\n👥 Users:")
#         self.stdout.write(f"   Registered: {registered_users}")
#         self.stdout.write(f"   Anonymous Sessions: {anonymous_sessions}")
        
#         # Language distribution
#         language_stats = UserPreference.objects.values('language').annotate(
#             count=Count('language')
#         ).order_by('-count')
        
#         self.stdout.write(f"\n🌐 Language Distribution:")
#         for stat in language_stats:
#             self.stdout.write(f"   {stat['language']}: {stat['count']}")
        
#         # Document types
#         doc_type_stats = LegalDocument.objects.values('document_type').annotate(
#             count=Count('document_type')
#         ).order_by('-count')
        
#         self.stdout.write(f"\n📋 Document Types:")
#         for stat in doc_type_stats:
#             type_display = dict(LegalDocument.DOCUMENT_TYPES).get(
#                 stat['document_type'], stat['document_type']
#             )
#             self.stdout.write(f"   {type_display}: {stat['count']}")
    
#     def migrate_sessions(self, user_id, session_keys):
#         """Migrate anonymous sessions to a user account"""
#         from django.contrib.auth.models import User
        
#         try:
#             user = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             self.stdout.write(
#                 self.style.ERROR(f"User with ID {user_id} not found")
#             )
#             return
        
#         self.stdout.write(f"🔄 Migrating sessions to user: {user.username}")
        
#         if not session_keys:
#             # Show available session keys
#             anonymous_prefs = UserPreference.objects.filter(
#                 user__isnull=True
#             ).values_list('session_key', flat=True)
            
#             self.stdout.write("Available session keys:")
#             for key in anonymous_prefs:
#                 self.stdout.write(f"   {key}")
#             return
        
#         migrated_count = 0
#         for session_key in session_keys:
#             try:
#                 # Migrate user preferences
#                 UserPreference.objects.filter(session_key=session_key).update(
#                     user=user, session_key=None
#                 )
                
#                 # Migrate documents
#                 LegalDocument.objects.filter(session_key=session_key).update(
#                     user=user, session_key=None
#                 )
                
#                 # Migrate chat sessions
#                 ChatSession.objects.filter(session_key=session_key).update(
#                     user=user, session_key=None
#                 )
                
#                 # Migrate analytics events
#                 AnalyticsEvent.objects.filter(session_key=session_key).update(
#                     user=user, session_key=None
#                 )
                
#                 migrated_count += 1
#                 self.stdout.write(f"   ✓ Migrated session: {session_key}")
                
#             except Exception as e:
#                 self.stdout.write(
#                     self.style.ERROR(f"   ✗ Failed to migrate {session_key}: {e}")
#                 )
        
#         self.stdout.write(
#             self.style.SUCCESS(f"Successfully migrated {migrated_count} sessions")
#         )