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


# ── Categories ──────────────────────────────────────────────
@role_required('staff')
def category_list(request):
    cats = Category.objects.select_related('cefr_level', 'color').order_by('order')
    return render(request, 'dashboard/categories/list.html', {'categories': cats})


@role_required('staff')
def category_add(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category added.')
        return redirect('dashboard_category_list')
    return render(request, 'dashboard/categories/form.html', {'form': form, 'action': 'Add'})


@role_required('staff')
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('dashboard_category_list')
    return render(request, 'dashboard/categories/form.html', {'form': form, 'action': 'Edit', 'obj': cat})


@role_required('staff')
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if cat.words.exists():
        messages.error(request, f'Cannot delete — {cat.words.count()} words still use this category. Reassign or delete them first.')
        return redirect('dashboard_category_list')
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted.')
        return redirect('dashboard_category_list')
    return render(request, 'dashboard/categories/list.html', {'categories': Category.objects.all(), 'confirm_delete': cat})


# ── Colors ──────────────────────────────────────────────────
@role_required('staff')
def color_list(request):
    colors = Color.objects.all()
    return render(request, 'dashboard/colors/list.html', {'colors': colors})


@role_required('staff')
def color_form(request, pk=None):
    instance = get_object_or_404(Color, pk=pk) if pk else None
    form = ColorForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Color saved.')
        return redirect('dashboard_color_list')
    return render(request, 'dashboard/colors/form.html', {'form': form, 'action': 'Edit' if pk else 'Add'})


# ── CEFR Levels ─────────────────────────────────────────────
@role_required('staff')
def cefr_list(request):
    levels = list(CEFRLevel.objects.order_by('order'))
    if request.method == 'POST':
        pk = int(request.POST.get('level_pk'))
        level = get_object_or_404(CEFRLevel, pk=pk)
        level.name = request.POST.get('name', level.name).strip()
        level.save(update_fields=['name'])
        messages.success(request, f'{level.code} updated.')
        return redirect('dashboard_cefr_list')
    return render(request, 'dashboard/cefr/list.html', {'levels': levels})
