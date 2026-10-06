from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s file ({self.id})"

class AnalysisResult(models.Model):
    # This links the result to the specific file that was analyzed.
    file = models.OneToOneField(UploadedFile, on_delete=models.CASCADE)
    
    # This will store the AI's full text summary
    result_text = models.TextField()
    
    # --- NEW FIELD ---
    # This will store the structured JSON for our colorful UI
    result_json = models.JSONField(null=True, blank=True)
    # --- END NEW FIELD ---
    
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.file.file.name}"
    
# ... (At the bottom of hub/models.py) ...

# --- RETAIL INSIGHT ENGINE MODELS ---

class RetailFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='retail_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # We will store the column names and data types as a JSON string
    # This is so the AI knows the "schema" of the file
    schema_json = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"RetailFile ({self.id}) for {self.user.username}"

class ChatMessage(models.Model):
    # Link to the specific retail file
    retail_file = models.ForeignKey(RetailFile, on_delete=models.CASCADE)
    
    # Store the message
    message = models.TextField()
    response = models.TextField(blank=True, null=True) # The AI's response
    
    # Who sent it?
    is_from_user = models.BooleanField(default=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message for {self.retail_file_id} (User: {self.is_from_user})"