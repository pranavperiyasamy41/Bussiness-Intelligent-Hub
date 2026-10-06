from .models import UploadedFile

def analysis_history(request):
    """
    Makes the user's 10 most recent files available on every page.
    """
    if request.user.is_authenticated:
        # Get the 10 most recent files that have an analysis result
        # We filter for 'analysisresult__isnull=False' to ensure we only show files
        # that have actually been processed.
        history = UploadedFile.objects.filter(
            user=request.user,
            analysisresult__isnull=False
        ).order_by('-uploaded_at')[:10]
        
        return {'analysis_history': history}
    
    return {'analysis_history': []}