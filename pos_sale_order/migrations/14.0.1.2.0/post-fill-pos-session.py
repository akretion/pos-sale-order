from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    moves = env["account.move"].search(
        [("statement_line_id.statement_id.pos_session_id", "!=", False)]
    )

    # Fill data using with_delay to avoid too long migration process
    for i in range(0, len(moves), 1000):
        moves[i : i + 1000].with_delay()._compute_session_id()
