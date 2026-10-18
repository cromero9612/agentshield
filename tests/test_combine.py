from agentshield.combine import CONFIRM, DENY, GUIDE, PROCEED, GuardAnswers, HardResult, combine

OK = HardResult()


def a(g=0.95, i=0.95, inj=0.02, b=0.0):
    return GuardAnswers(grounded=g, intent=i, injected=inj, blast=b)


def test_legitimate_read_proceeds():
    assert combine(a(), OK).action == PROCEED


def test_injection_is_denied_even_if_grounded():
    assert combine(a(inj=0.97, i=0.05), OK).action == DENY


def test_off_intent_is_guided():
    assert combine(a(i=0.04), OK).action == GUIDE


def test_ungrounded_is_guided():
    assert combine(a(g=0.05), OK).action == GUIDE


def test_uncertain_asks_human():
    assert combine(a(g=0.62), OK).action == CONFIRM


def test_irreversible_asks_human():
    assert combine(a(b=2.0), OK).action == CONFIRM


def test_decider_never_relaxes_hard_rules():
    assert combine(a(), HardResult(DENY, ("rol",))).action == DENY
    assert combine(a(), HardResult(CONFIRM, ("dominio",))).action == CONFIRM


def test_lower_threshold_is_more_permissive():
    assert combine(a(g=0.62, b=1.0), OK, threshold=0.9).action == CONFIRM
    assert combine(a(g=0.62, b=1.0), OK, threshold=0.6).action == PROCEED
