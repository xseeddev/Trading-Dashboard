from django.shortcuts import render
from TradingDashbackend.core.logger import setup_logger

logg = setup_logger("Core:Views")

def index(request):
    
    context = {
        "title": "Django example",
    }
    logg.debug("Test 1")
    return render(request, "index.html", context)
