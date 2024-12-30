from django.http import JsonResponse
from django.shortcuts import render

# Render the homepage
def home(request):
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')
        response_data = {
            'user_input': user_input,
            'response': f"You said: {user_input}. Here is a dummy response."
        }
        return JsonResponse(response_data)
    return render(request, 'home.html')