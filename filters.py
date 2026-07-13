# filters.py

def filter_by_pincode(query, user_profile):
    """Return only jobs whose employer pincode matches the jobseeker's pincode."""
    if user_profile and user_profile.pincode:
        from models import Job
        return query.filter(Job.employer_pincode == user_profile.pincode)
    return query


def filter_by_job_types(query, job_types_str):
    """Filter by comma‑separated job types."""
    if not job_types_str:
        return query
    types = [t.strip() for t in job_types_str.split(',') if t.strip()]
    if types:
        from models import Job
        return query.filter(Job.job_type.in_(types))
    return query


def filter_by_city(query, city):
    """Filter by employer city."""
    if city:
        from models import Job
        return query.filter(Job.employer_city == city)
    return query


def filter_by_state(query, state):
    """Filter by employer state."""
    if state:
        from models import Job
        return query.filter(Job.employer_state.ilike(f'%{state}%'))
    return query


def filter_by_min_vacancies(query, min_vac):
    """Show only jobs with at least this many vacancies."""
    if min_vac and min_vac.isdigit():
        from models import Job
        return query.filter(Job.vacancies >= int(min_vac))
    return query


def filter_by_search(query, keyword):
    """Search in job name, description, salary, and location."""
    if keyword:
        from models import Job
        pattern = f'%{keyword}%'
        return query.filter(
            Job.job_name.ilike(pattern) |
            Job.job_description.ilike(pattern) |
            Job.committed_salary.ilike(pattern) |
            Job.location.ilike(pattern)
        )
    return query