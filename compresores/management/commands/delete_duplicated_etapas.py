from django.core.management.base import BaseCommand
from compresores.models import Compresor, EtapaCompresor, LadoEtapaCompresor

class Command(BaseCommand):
    help = 'Delete duplicated etapas for a specific compresor'

    def handle(self, *args, **kwargs):
        
        tag = "102-J"
        try:
            compresor = Compresor.objects.get(tag=tag)
        except Compresor.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Compresor with tag '{tag}' does not exist."))
            return

       
        for caso in compresor.casos.all():
            etapas = EtapaCompresor.objects.filter(compresor=caso)
            for etapa in etapas:
                if etapas.filter(numero=etapa.numero).count() > 1:
                    lados = LadoEtapaCompresor.objects.filter(etapa=etapa)
                    for lado in lados:
                        lado.delete()
                    etapa.delete()

        self.stdout.write(self.style.SUCCESS(f"Duplicated etapas for compresor '{tag}' have been deleted."))
