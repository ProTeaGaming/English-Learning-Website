from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from accounts.decorators import role_required
from django.contrib.auth import get_user_model
from vocab.models import Word, Category, CEFRLevel, Color
from .forms import WordForm, CategoryForm, ColorForm, CEFRForm, UserRoleForm


@role_required('staff')
def index(request):
    context = {
        'word_count':     Word.objects.count(),
        'category_count': Category.objects.count(),
        'cefr_count':     CEFRLevel.objects.count(),
        'color_count':    Color.objects.count(),
        'user_count':     get_user_model().objects.count(),
    }
    return render(request, 'dashboard/index.html', context)


@role_required('staff')
def word_list(request):
    category_id = request.GET.get('category')
    cefr_code   = request.GET.get('cefr')
    qs = Word.objects.select_related('category', 'cefr_level').order_by('category__order', 'order')
    if category_id:
        qs = qs.filter(category_id=category_id)
    if cefr_code:
        qs = qs.filter(cefr_level__code=cefr_code)
    context = {
        'words':      qs,
        'categories': Category.objects.all(),
        'cefr_levels': CEFRLevel.objects.all(),
        'selected_cat':  category_id,
        'selected_cefr': cefr_code,
    }
    return render(request, 'dashboard/words/list.html', context)


@role_required('staff')
def word_add(request):
    form = WordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Word added.')
        return redirect('dashboard_word_list')
    return render(request, 'dashboard/words/form.html', {'form': form, 'action': 'Add'})


@role_required('staff')
def word_edit(request, pk):
    word = get_object_or_404(Word, pk=pk)
    form = WordForm(request.POST or None, instance=word)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Word updated.')
        return redirect('dashboard_word_list')
    return render(request, 'dashboard/words/form.html', {'form': form, 'action': 'Edit', 'obj': word})


@role_required('staff')
def word_delete(request, pk):
    word = get_object_or_404(Word, pk=pk)
    if request.method == 'POST':
        word.delete()
        messages.success(request, 'Word deleted.')
        return redirect('dashboard_word_list')
    return render(request, 'dashboard/words/list.html', {'confirm_delete': word})
