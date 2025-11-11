import sys, os
import logging

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app, db
from models import Feedback
from services.feedback_classifier import FeedbackClassifier


def main():
    app = create_app()
    with app.app_context():
        clf = FeedbackClassifier()
        updated_kind = 0
        updated_severity = 0
        total = 0
        for fb in Feedback.query.all():
            total += 1
            result = clf.classify(fb.title or '', fb.description or '')
            # update kind if confidence is high enough
            if result['confidence'] >= 0.7 and (fb.kind != result['label']):
                old_kind = fb.kind
                fb.kind = result['label']
                updated_kind += 1
                logging.info(f"Update kind ID {fb.id}: {old_kind} -> {fb.kind} ({result['confidence']:.0%})")
            # update severity and confidence (no downgrade)
            sev = result['severity']
            sc = result['severity_confidence']
            if fb.severity != sev or (fb.severity_confidence != sc):
                old_sev = fb.severity
                fb.severity = sev
                fb.severity_confidence = sc
                updated_severity += 1
                logging.info(f"Update severity ID {fb.id}: {old_sev} -> {sev} ({sc:.0%})")
            db.session.add(fb)
            db.session.commit()
        print(f"Checked {total} items; updated {updated_kind} kinds and {updated_severity} severities.")


if __name__ == "__main__":
    main()