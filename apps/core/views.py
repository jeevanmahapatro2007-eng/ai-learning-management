from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import render, redirect

from .forms import ContactForm
from .models import FAQ
from apps.courses.models import Course, Category


def home(request):
    featured_courses = (
        Course.objects.filter(status=Course.Status.PUBLISHED)
        .annotate(enrolled_count=Count('enrollments'))
        .order_by('-enrolled_count', '-created_at')[:6]
    )
    categories = Category.objects.annotate(
        course_count=Count('courses', filter=Q(courses__status=Course.Status.PUBLISHED))
    ).filter(course_count__gt=0)[:8]

    stats = {
        'course_count': Course.objects.filter(status=Course.Status.PUBLISHED).count(),
        'category_count': Category.objects.count(),
    }

    return render(request, 'core/home.html', {
        'featured_courses': featured_courses,
        'categories': categories,
        'stats': stats,
    })


def about(request):
    return render(request, 'core/about.html')


def faq(request):
    faqs = FAQ.objects.all()
    return render(request, 'core/faq.html', {'faqs': faqs})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thanks — your message has been sent. We will get back to you soon.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})
