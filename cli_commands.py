import click
from app_init import db, custom_cli
from models import SentEmail, Policy, Signature

@custom_cli.command("rensa-skickade-paminda")
@click.argument("klubb")
def rensa_skickade_paminda_command(klubb):
    print(f"Kommandot körs för klubb: {klubb}")
    try:
        from app_init import app
        with app.app_context():
            deleted = SentEmail.query.filter(
                SentEmail.klubb == klubb,
                SentEmail.status.in_(["Skickad", "Påmind"])
            ).delete(synchronize_session='fetch')
            db.session.commit()
            click.echo(f"Raderade {deleted} skickade och påminda poster för klubb: {klubb}")
    except Exception as e:
        click.echo(f"Ett fel uppstod: {str(e)}")

@custom_cli.command("add-policy")
@click.argument("klubb")
@click.argument("filväg", type=click.Path(exists=True))
def lägg_till_policy_command(klubb, filväg):
    try:
        from app_init import app
        import json
        with app.app_context():
            with open(filväg, 'r', encoding='utf-8') as fil:
                policy_content = json.load(fil)
            
            ny_policy = Policy(klubb=klubb, policy_content=json.dumps(policy_content))
            db.session.add(ny_policy)
            db.session.commit()
            click.echo(f"En ny policy har lagts till för klubben '{klubb}' från filen '{filväg}'.")
    except Exception as e:
        click.echo(f"Ett fel uppstod vid tillägg av policy för klubb '{klubb}': {str(e)}")


@custom_cli.command("delete-club")
@click.argument("klubb")
def delete_club_command(klubb):
    try:
        from app_init import app
        with app.app_context():
            # Kontrollera om klubben existerar innan vi försöker ta bort den
            club_exists = db.session.query(
                (Policy.query.filter_by(klubb=klubb).exists()) |
                (Signature.query.filter_by(klubb=klubb).exists()) |
                (SentEmail.query.filter_by(klubb=klubb).exists())
            ).scalar()

            if not club_exists:
                click.echo(f"Klubben '{klubb}' hittades inte i databasen.")
                return

            result = delete_club(klubb)
            click.echo(f"Klubb '{klubb}' har tagits bort.")
            click.echo(f"Borttagna poster: {result['policies']} policys, {result['signatures']} signaturer, {result['sent_emails']} skickade e-postmeddelanden.")
    except Exception as e:
        click.echo(f"Ett fel uppstod vid borttagning av klubb '{klubb}': {str(e)}")

def delete_club(klubb):
    try:
        # Använd LIKE för att matcha klubbnamn som börjar med det givna namnet
        deleted_policies = Policy.query.filter(Policy.klubb.like(f"{klubb}%")).delete()
        deleted_signatures = Signature.query.filter(Signature.klubb.like(f"{klubb}%")).delete()
        deleted_sent_emails = SentEmail.query.filter(SentEmail.klubb.like(f"{klubb}%")).delete()

        db.session.commit()

        return {
            'policies': deleted_policies,
            'signatures': deleted_signatures,
            'sent_emails': deleted_sent_emails
        }
    except Exception as e:
        db.session.rollback()
        click.echo(f"Fel vid borttagning av klubb {klubb}: {str(e)}")
        raise
