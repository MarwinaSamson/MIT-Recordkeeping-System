# UserProfile.is_active — align ORM with DB (NOT NULL column may already exist).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students_app", "0010_studentinboxmessage"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="userprofile",
                    name="is_active",
                    field=models.BooleanField(default=False),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=r"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = current_schema()
                              AND table_name = 'students_app_userprofile'
                              AND column_name = 'is_active'
                        ) THEN
                            ALTER TABLE students_app_userprofile
                                ADD COLUMN is_active boolean NOT NULL DEFAULT false;
                            UPDATE students_app_userprofile p
                            SET is_active = u.is_active
                            FROM auth_user u
                            WHERE p.user_id = u.id;
                        ELSE
                            UPDATE students_app_userprofile p
                            SET is_active = u.is_active
                            FROM auth_user u
                            WHERE p.user_id = u.id AND p.is_active IS NULL;
                            ALTER TABLE students_app_userprofile
                                ALTER COLUMN is_active SET DEFAULT false;
                            ALTER TABLE students_app_userprofile
                                ALTER COLUMN is_active SET NOT NULL;
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
