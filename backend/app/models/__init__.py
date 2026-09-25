"""Import every model module here so that Base.metadata sees all tables
before Alembic autogenerate or Base.metadata.create_all() runs."""

from app.models.user_models import User, UserProfile, Account, Category  # noqa: F401
from app.models.finance_models import Transaction, Budget, SavingsGoal, GoalContribution  # noqa: F401
from app.models.investment_models import Investment, RecurringTransaction, CategoryRule  # noqa: F401
from app.models.import_models import ImportedFile, ImportBatch, ImportError_  # noqa: F401
from app.models.system_models import Prediction, Notification, UserSettings, AuditLog  # noqa: F401
