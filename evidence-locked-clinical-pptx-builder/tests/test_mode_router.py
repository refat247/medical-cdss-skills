from scripts.mode_router import route
def test_modes():
    assert route('build a case based deck')['mode']=='BUILD_CASE_BASED'
    assert route('audit this deck')['mode']=='INSPECT'
    assert route('make a 45 min derivative')['mode']=='DERIVATIVE_BUILD'
    assert route('anything',project_status='closed')['mode']=='MAINTENANCE'
