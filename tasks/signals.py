from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Task, TaskAttachment

# --- SYNC ON ATTACHMENT SAVE ---
@receiver(post_save, sender=TaskAttachment)
def sync_child_attachment_to_parent(sender, instance, created, **kwargs):
    task = instance.task
    if not task or not task.parent_task:
        return

    parent = task.parent_task
    # If child is Completed, ensure all attachments exist in parent
    if task.status == 'Completed':
        # Copy this single attachment (if missing)
        if not parent.attachments.filter(file=instance.file.name).exists():
            TaskAttachment.objects.create(
                task=parent,
                file=instance.file,
                uploaded_by=instance.uploaded_by,
                Output=instance.Output
            )
        # Optional: recheck all attachments (force full sync)
        sync_all_child_attachments(task, parent)

# --- REMOVE ATTACHMENT WHEN CHILD DELETES IT ---
@receiver(post_delete, sender=TaskAttachment)
def remove_child_attachment_from_parent(sender, instance, **kwargs):
    task = instance.task
    if not task or not task.parent_task:
        return
    parent = task.parent_task
    parent.attachments.filter(file=instance.file.name).delete()

# --- HELPER FUNCTION: full resync (handles missing ones) ---
def sync_all_child_attachments(child_task, parent_task):
    child_attachments = child_task.attachments.all()
    for attach in child_attachments:
        if not parent_task.attachments.filter(file=attach.file.name).exists():
            TaskAttachment.objects.create(
                task=parent_task,
                file=attach.file,
                uploaded_by=attach.uploaded_by,
                 Output=attach.Output
            )
