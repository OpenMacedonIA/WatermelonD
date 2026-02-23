import logging
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
import subprocess
import time

# Logger
logger = logging.getLogger("SchedulerManager")

class SchedulerManager:
    def __init__(self, app=None):
        self.scheduler = APScheduler()
        self.app = app
        
        # Configuration
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Inicializa el programador de tareas con la app de Flask."""
        self.app = app
        
        # Configuración de persistencia (SQLite)
        # APScheduler usa esto para guardar jobs entre reinicios
        app.config['SCHEDULER_JOBSTORES'] = {
            'default': SQLAlchemyJobStore(url='sqlite:///database/jobs.sqlite')
        }
        app.config['SCHEDULER_API_ENABLED'] = True # Punto de acceso /scheduler/jobs activado por defecto en Flask-APScheduler, pero podríamos construir nuestra propia API
        app.config['SCHEDULER_TIMEZONE'] = "Europe/Madrid" # Ajustar según config?

        self.scheduler.init_app(app)
        self.scheduler.start()
        logger.info("Scheduler started.")

    # --- Funciones de Job Permitidas ---
    # Estas deben ser, idealmente, estáticas o independientes para que se puedan serializar/llamar fácilmente, 
    # pero los métodos de la instancia funcional si la instancia es global.
    # Flask-APScheduler normalmente busca 'func' como la ruta del string 'module:function'.
    
    def add_bash_job(self, name, command, cron_expression):
        """
        Añade un trabajo cron (cron job) que ejecuta un comando bash.
        cron_expression: formato de string "minuto hora día mes día_de_la_semana" (cron estándar)
                         O parámetros específicos como "*/5 * * * *"
        """
        # Analiza el string cron "min hour day month dow"
        # Ejemplo: "0 3 * * 2" -> A las 03:00 del martes.
        
        try:
            parts = cron_expression.split()
            if len(parts) != 5:
                return False, "Formato cron inválido. Se esperan 5 partes: min hora día mes día_semana"
            
            minute, hour, day, month, day_of_week = parts
            
            # Crea un ID único
            job_id = f"job_{int(time.time())}_{name.replace(' ', '_')}"
            
            self.scheduler.add_job(
                id=job_id,
                func='modules.scheduler_manager:run_bash_command', # Referencia string
                args=[command],
                trigger=CronTrigger(
                    minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week
                ),
                name=name,
                replace_existing=True
            )
            return True, f"Job {name} added."
            
        except Exception as e:
            logger.error(f"Error adding job: {e}")
            return False, str(e)

    def delete_job(self, job_id):
        try:
            self.scheduler.remove_job(job_id)
            return True, "Job deleted."
        except Exception as e:
            return False, str(e)
            
    def get_jobs(self):
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': str(job.next_run_time),
                'trigger': str(job.trigger)
            })
        return jobs

# --- Funciones independientes para los Jobs ---
def run_bash_command(command):
    """Ejecuta un comando bash y loguea el resultado."""
    try:
        logger.info(f"Executing Scheduled Job: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        logger.info(f"Job Output: {result.stdout}")
        if result.stderr:
            logger.warning(f"Job Stderr: {result.stderr}")
    except Exception as e:
        logger.error(f"Job Execution Error: {e}")
