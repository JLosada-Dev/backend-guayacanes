"""
Carga los barrios de Popayán organizados por comuna.
Fuente: POT Popayán / historiadepopa.blogspot.com (verificado contra PDF U-2/56)

Uso:
    uv run python manage.py load_neighborhoods
    uv run python manage.py load_neighborhoods --clear   # borra existentes antes de cargar
"""
from django.core.management.base import BaseCommand
from apps.core.models import Commune, Neighborhood

NEIGHBORHOODS_BY_COMMUNE = {
    1: [
        "Alcalá", "Antonio Nariño", "Belalcázar", "Bloque Pubenza", "Campamento",
        "Campo Bello", "Capri", "Casas Fiscales", "Catay", "El Nogal",
        "El Recuerdo", "Fancal", "La Cabaña", "La Playa", "La Villa",
        "Loma Linda", "Los Laureles", "Los Rosales", "Machangara", "María Alexandra",
        "Modelo", "Monte Rosales", "Nueva Granada", "Nuevo Catay",
        "Plazuela del Poblado", "Prados Norte", "Puerta Hierro", "Santa Clara",
        "Villa Paula",
    ],
    2: [
        "Alto de Cauca", "Ana Lucía", "Atardecer Pradera", "Balcón Norte",
        "Bella Vista", "Bello Horizonte", "Bosques del Pinar", "Canal Brujas",
        "Canterbury", "Chamizal", "Coomeva", "Cruz Roja", "Destechados del Norte",
        "El Bambú", "El Pinar", "El Placer", "El Tablazo", "El Uvo",
        "Esperanza Norte", "Galilea", "Guayacanes del Río", "Hogares Comunitarios",
        "La Aldea", "La Arboleda", "La Aurora", "La Cordillera", "La Florida",
        "La Primavera", "Los Cámbulos", "Los Pinares", "Los Ángeles",
        "Luna Blanca", "Lusitania", "María Paz", "Matamoros", "Morinda",
        "Nueva Alianza", "Nueva Integración", "Nuevo Tequendama",
        "Pinares del Río", "Pino Pardo", "Pinos Llanos", "Rincón La Aldea",
        "Rincón Primavera", "Río Vista", "San Fernando", "San Ignacio",
        "San Miguel", "Santiago de Cali", "Trece de Octubre", "Tóez",
        "Villa Andrés", "Villa Claudia", "Villa González", "Villa Inés",
        "Villa Melisa", "Villa Norte", "Villa Vista", "Villa del Viento",
        "Zuldemaida",
    ],
    3: [
        "Acacias", "Alicante I", "Alicante II", "Alto Bajo Cauca",
        "Altos del Jardín", "Altos del Río", "Arco Yanaconas", "Aída Lucía",
        "Bolívar", "Chicalá Estancia", "Ciudad Jardín", "Deportistas",
        "Encocauca", "Galicia", "Guayacanes", "José A. Galán", "La Estancia",
        "La Virginia", "La Ximena", "Los Hoyos", "Moravia", "Nuevo Yambitará",
        "Palacé", "Periodistas", "Plazuela del Poblado", "Portales Estancia",
        "Portales Norte", "Portón Hacienda", "Portón Yanaconas", "Pueblillo",
        "Recodo del Río", "Rincón Estancia", "Rincón Yambitará",
        "Rincón de La Ximena", "Rincón del Río", "Sotará", "Torres del Río",
        "Tres Margaritas", "Ucrania", "Vega de Prieto", "Villa Alicia",
        "Villa Mercedes", "Yambitará", "Yanaconas", "Yanagual",
    ],
    4: [
        "Argentina", "Bosques de Pomona", "Caldas", "Centro", "Colombia I",
        "Colombia II", "Edificio Dorado", "El Achiral", "El Cadillal",
        "El Empedrado", "El Liceo", "El Patio", "El Prado", "El Refugio",
        "Fucha", "Hernando Lora", "La Pamba", "Las Américas", "Loma de Cartagena",
        "Los Álamos", "Moscopán", "Obrero", "Pomona", "Provitec I Etapa",
        "Provitec II Etapa", "San Camilo", "San Rafael Viejo", "Santa Catalina",
        "Santa Inés", "Santa Teresita", "Siglo XX", "Valencia", "Vásquez Cobo",
    ],
    5: [
        "Alameda", "Avelino Ull", "Berlín", "Braceros", "Colgate Palmolive",
        "El Lago", "El Plateado", "El Poblado Alto", "La Campiña", "La Floresta",
        "Las Ferias", "Los Andes", "Los Sauces", "María Oriente",
        "Nueva Venecia", "Santa Mónica", "Suizo",
    ],
    6: [
        "Alfonso López", "Calicanto", "Comuneros", "El Boquerón", "El Dean",
        "El Limonar", "El Pajonal", "Gabriel García Márquez", "Jorge E. Gaitán",
        "José H. López", "La Colina", "La Gran Victoria", "La Ladera",
        "La Paz Sur", "Las Veraneras", "Loma de La Virgen", "Los Naranjos",
        "Los Tejares", "Madres Solteras", "Manuela Beltrán", "Nueva Granada",
        "Nuevo Japón", "Nuevo País", "Primero de Mayo", "San Rafael Nuevo",
        "Santa Fe", "Sindicato I y II Etapa", "Tejares de Otón", "Valparaíso",
        "Versalles", "Versalles Pajonal", "Villa Carmen II", "Villa del Sur",
    ],
    7: [
        "Campiña-Retiro", "Chapinero", "Corsocial", "Domingo Sabio",
        "El Minuto de Dios", "El Mirador", "Ibero Tierra", "Independencia",
        "Isabela I", "Isabela II", "La Conquista", "La Heroica", "La Libertad",
        "La Unión", "Las Brisas", "Las Palmas I", "Las Palmas II", "Las Vegas",
        "Los Campos", "Madres Desamparadas", "Nazareth",
        "Niño Jesús de Praga-Retiro", "Nuevo Berrío", "Nuevo Popayán",
        "Panamericana", "Retiro Alto y Bajo", "San Fernando", "Santa Librada",
        "Solidaridad", "Tomás Cipriano", "Treinta y Uno de Marzo",
        "Villa Occidente", "Villa del Carmen I",
    ],
    8: [
        "Asoprecom", "Camilo Torres", "Canadá", "Edificio Llano Largo",
        "El Guayabal", "El Triunfo", "El Zaguán", "José M. Obando", "Junín",
        "La Esmeralda", "La Esperanza", "La Isla", "La Victoria", "Llano Largo",
        "Los Libertadores", "Minuto de Dios", "Pandiguando", "Popular",
        "Santa Helena",
    ],
    9: [
        "Carlos Primero", "Cinco de Abril", "Kennedy", "La Capitana",
        "La Gaitana", "La Sombrilla", "Lomas de Granada", "Los Naranjos",
        "María Occidente", "Mis Ranchitos", "Nuevo Hogar",
        "San Antonio de Padua", "San José", "San Miguel", "Urapanes del Río",
    ],
}


class Command(BaseCommand):
    help = "Carga barrios de Popayán por comuna (sin polígono)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Elimina todos los barrios existentes antes de cargar",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            deleted, _ = Neighborhood.objects.all().delete()
            self.stdout.write(f"  Eliminados {deleted} barrios existentes.")

        # Precargar comunas por número
        communes = {c.number: c for c in Commune.objects.all()}
        if not communes:
            self.stderr.write(self.style.ERROR(
                "No hay comunas cargadas. Ejecuta primero: manage.py load_communes"
            ))
            return

        created = 0
        skipped = 0
        for commune_number, barrios in NEIGHBORHOODS_BY_COMMUNE.items():
            commune = communes.get(commune_number)
            if not commune:
                self.stderr.write(self.style.WARNING(
                    f"  Comuna {commune_number} no encontrada, saltando {len(barrios)} barrios."
                ))
                skipped += len(barrios)
                continue

            for name in barrios:
                _, was_created = Neighborhood.objects.get_or_create(
                    name=name,
                    commune=commune,
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"  {created} barrios creados, {skipped} ya existían."
        ))
        total = Neighborhood.objects.count()
        self.stdout.write(f"  Total barrios en BD: {total}")
