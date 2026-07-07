from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from accounts.decorators import role_required
from django.contrib.auth import get_user_model
from vocab.models import Word, Category, CEFRLevel, Color, GrammarTopic, GrammarLessonBlock, GrammarQuestion
from .forms import (WordForm, CategoryForm, ColorForm, CEFRForm, UserRoleForm,
                    GrammarTopicForm, GrammarLessonBlockForm, GrammarQuestionForm)


@role_required('staff')
def index(request):
    context = {
        'word_count':     Word.objects.count(),
        'category_count': Category.objects.count(),
        'cefr_count':     CEFRLevel.objects.count(),
        'color_count':    Color.objects.count(),
        'user_count':     get_user_model().objects.count(),
        'grammar_count': GrammarTopic.objects.count(),
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


# ── Users ────────────────────────────────────────────────────
@role_required('admin')
def user_list(request):
    query = request.GET.get('q', '')
    User  = get_user_model()
    users = User.objects.order_by('email')
    if query:
        users = (users.filter(email__icontains=query) | users.filter(username__icontains=query)).distinct()
    return render(request, 'dashboard/users/list.html', {'users': users, 'query': query})


@role_required('admin')
def user_detail(request, pk):
    User       = get_user_model()
    target     = get_object_or_404(User, pk=pk)
    form       = UserRoleForm(request.POST or None, initial={
        'role': target.role, 'is_active': target.is_active
    })
    if request.method == 'POST' and form.is_valid():
        new_role      = form.cleaned_data['role']
        new_is_active = form.cleaned_data.get('is_active', False)

        # Guard against an admin locking themselves out of management.
        if target == request.user:
            if not new_is_active:
                messages.error(request, 'You cannot deactivate your own account.')
                return redirect('dashboard_user_detail', pk=target.pk)
            if new_role != 'admin':
                messages.error(request, 'You cannot demote your own admin role.')
                return redirect('dashboard_user_detail', pk=target.pk)

        # Guard against removing the last active admin (demotion or deactivation).
        demoting_admin = target.role == 'admin' and (new_role != 'admin' or not new_is_active)
        if demoting_admin:
            active_admins = User.objects.filter(role='admin', is_active=True).count()
            if active_admins <= 1:
                messages.error(request, 'You cannot remove the last active admin.')
                return redirect('dashboard_user_detail', pk=target.pk)

        target.role      = new_role
        target.is_active = new_is_active
        target.save(update_fields=['role', 'is_active'])
        messages.success(request, f'{target.email} updated.')
        return redirect('dashboard_user_list')
    return render(request, 'dashboard/users/detail.html', {'target': target, 'form': form})


# ── Grammar ─────────────────────────────────────────────────
@role_required('staff')
def grammar_topic_list(request):
    stage = request.GET.get('stage', '')
    qs = GrammarTopic.objects.order_by('order')
    if stage:
        qs = qs.filter(stage=stage)
    return render(request, 'dashboard/grammar/list.html', {
        'topics': qs, 'stages': GrammarTopic.STAGES, 'selected_stage': stage,
    })


@role_required('staff')
def grammar_topic_add(request):
    form = GrammarTopicForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Grammar topic added.')
        return redirect('dashboard_grammar_list')
    return render(request, 'dashboard/grammar/form.html', {'form': form, 'action': 'Add'})


@role_required('staff')
def grammar_topic_edit(request, pk):
    topic = get_object_or_404(GrammarTopic, pk=pk)
    form = GrammarTopicForm(request.POST or None, instance=topic)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Grammar topic updated.')
        return redirect('dashboard_grammar_list')
    return render(request, 'dashboard/grammar/form.html', {'form': form, 'action': 'Edit', 'obj': topic})


@role_required('staff')
def grammar_topic_delete(request, pk):
    topic = get_object_or_404(GrammarTopic, pk=pk)
    if request.method == 'POST':
        topic.delete()
        messages.success(request, 'Grammar topic deleted (with its blocks and questions).')
        return redirect('dashboard_grammar_list')
    return render(request, 'dashboard/grammar/list.html', {
        'topics': GrammarTopic.objects.order_by('order'),
        'stages': GrammarTopic.STAGES, 'selected_stage': '',
        'confirm_delete': topic,
    })


@role_required('staff')
def grammar_block_list(request, topic_pk):
    topic = get_object_or_404(GrammarTopic, pk=topic_pk)
    return render(request, 'dashboard/grammar/blocks.html', {'topic': topic, 'blocks': topic.blocks.all()})


@role_required('staff')
def grammar_block_add(request, topic_pk):
    topic = get_object_or_404(GrammarTopic, pk=topic_pk)
    form = GrammarLessonBlockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        block = form.save(commit=False)
        block.topic = topic
        block.save()
        messages.success(request, 'Lesson block added.')
        return redirect('dashboard_grammar_blocks', topic_pk=topic.pk)
    return render(request, 'dashboard/grammar/block_form.html', {'form': form, 'action': 'Add', 'topic': topic})


@role_required('staff')
def grammar_block_edit(request, pk):
    block = get_object_or_404(GrammarLessonBlock, pk=pk)
    form = GrammarLessonBlockForm(request.POST or None, instance=block)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lesson block updated.')
        return redirect('dashboard_grammar_blocks', topic_pk=block.topic_id)
    return render(request, 'dashboard/grammar/block_form.html', {'form': form, 'action': 'Edit', 'topic': block.topic})


@role_required('staff')
def grammar_block_delete(request, pk):
    block = get_object_or_404(GrammarLessonBlock, pk=pk)
    topic_pk = block.topic_id
    if request.method == 'POST':
        block.delete()
        messages.success(request, 'Lesson block deleted.')
    return redirect('dashboard_grammar_blocks', topic_pk=topic_pk)


@role_required('staff')
def grammar_question_list(request, topic_pk):
    topic = get_object_or_404(GrammarTopic, pk=topic_pk)
    return render(request, 'dashboard/grammar/questions.html', {'topic': topic, 'questions': topic.questions.all()})


@role_required('staff')
def grammar_question_add(request, topic_pk):
    topic = get_object_or_404(GrammarTopic, pk=topic_pk)
    form = GrammarQuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        question = form.save(commit=False)
        question.topic = topic
        question.save()
        messages.success(request, 'Question added.')
        return redirect('dashboard_grammar_questions', topic_pk=topic.pk)
    return render(request, 'dashboard/grammar/question_form.html', {'form': form, 'action': 'Add', 'topic': topic})


@role_required('staff')
def grammar_question_edit(request, pk):
    question = get_object_or_404(GrammarQuestion, pk=pk)
    form = GrammarQuestionForm(request.POST or None, instance=question)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Question updated.')
        return redirect('dashboard_grammar_questions', topic_pk=question.topic_id)
    return render(request, 'dashboard/grammar/question_form.html', {'form': form, 'action': 'Edit', 'topic': question.topic})


@role_required('staff')
def grammar_question_delete(request, pk):
    question = get_object_or_404(GrammarQuestion, pk=pk)
    topic_pk = question.topic_id
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted.')
    return redirect('dashboard_grammar_questions', topic_pk=topic_pk)
