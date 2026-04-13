from django.http import Http404

from .models import ProjectMember


def get_project_membership(request, project_pk):
    """Return the ProjectMember for request.user in the given project, or raise Http404."""
    try:
        return ProjectMember.objects.select_related("project").get(
            project_id=project_pk,
            user=request.user,
        )
    except ProjectMember.DoesNotExist:
        raise Http404
