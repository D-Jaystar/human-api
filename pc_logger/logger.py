import time
from datetime import datetime, timezone
import httpx

try:
    from pc_logger.tracker import get_active_window_info
    from pc_logger.idle import is_user_afk
except ModuleNotFoundError:
    from tracker import get_active_window_info
    from idle import is_user_afk


class PCLogger:
    """
    De centrale computer-logger die op de achtergrond draait.
    Houdt per tijdblok bij welke applicatie actief is en detecteert context switches en AFK-status.
    """

    def __init__(
        self,
        device_id: str,
        token: str,
        api_url: str = "http://127.0.0.1:8000",
        poll_interval: float = 1.0,
        afk_threshold_sec: int = 180,
        max_block_sec: int = 300,
    ):
        self.device_id = device_id
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.poll_interval = poll_interval
        self.afk_threshold_sec = afk_threshold_sec
        self.max_block_sec = max_block_sec

        # Status van de logger loop
        self.is_running: bool = False

        # Huidige actieve sessieblok
        self.current_app: str | None = None
        self.current_title: str | None = None
        self.current_afk: bool = False
        self.block_start_time: datetime | None = None

        # Offline buffer / wachtrij voor als de server even niet bereikbaar is
        self.offline_queue: list[dict] = []

    def send_to_api(self, payload: dict) -> bool:
        """
        Verstuurt een activiteitsblok naar de Human API server met Bearer token.
        Als de server offline is of een fout geeft, wordt het blok in een lokale buffer bewaard.
        """
        endpoint = f"{self.api_url}/api/activity"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.post(endpoint, json=payload, headers=headers)
                if response.status_code == 200:
                    return True
                print(f"[LOGGER] API fout {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[LOGGER] Kan niet verzenden ({e}).")

        self.offline_queue.append(payload)
        return False

    def flush_offline_queue(self) -> None:
        """
        Probeert gebufferde offline logs alsnog te versturen.
        Stopt direct als de server nog steeds offline blijkt.
        """
        if not self.offline_queue:
            return

        to_send = list(self.offline_queue)
        self.offline_queue = []

        endpoint = f"{self.api_url}/api/activity"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        for idx, payload in enumerate(to_send):
            try:
                with httpx.Client(timeout=2.0) as client:
                    res = client.post(endpoint, json=payload, headers=headers)
                    if res.status_code != 200:
                        # Terugplaatsen van niet-verzonden items
                        self.offline_queue.extend(to_send[idx:])
                        break
            except Exception:
                # Server is nog offline, stop pogingen en bewaar rest van queue
                self.offline_queue.extend(to_send[idx:])
                break

    def flush_current_block(self) -> None:
        """
        Rondt het huidige tijdsblok af en stuurt het naar de API.
        """
        if self.current_app is None or self.block_start_time is None:
            return

        now = datetime.now(timezone.utc)
        duration_sec = int((now - self.block_start_time).total_seconds())

        # Negeer micro-flitsen van 0 seconden
        if duration_sec <= 0:
            return

        payload = {
            "device_id": self.device_id,
            "app_name": self.current_app,
            "window_title": self.current_title or "Onbekend",
            "is_afk": self.current_afk,
            "start_time": self.block_start_time.isoformat(),
            "end_time": now.isoformat(),
            "duration_sec": duration_sec,
        }

        status_str = "AFK" if self.current_afk else "Actief"
        title_preview = (self.current_title or "Onbekend")[:40]
        print(f"[LOG] {status_str} | {self.current_app} ({duration_sec}s) - {title_preview}")
        self.send_to_api(payload)

    def step(self) -> None:
        """
        Eén enkele inspectiecyclus:
        Controleert voorgrondvenster en AFK-status.
        Bij een wisseling (context switch) wordt het vorige blok weggeschreven en een nieuw gestart.
        """
        window_info = get_active_window_info()
        app_name = window_info["app_name"]
        title = window_info["window_title"]
        afk = is_user_afk(self.afk_threshold_sec)

        now = datetime.now(timezone.utc)

        # Eerste keer opstarten
        if self.current_app is None:
            self.current_app = app_name
            self.current_title = title
            self.current_afk = afk
            self.block_start_time = now
            return

        # Controleer of er gewisseld is van app, venstertitel of AFK-status
        has_context_switched = (app_name != self.current_app) or (title != self.current_title)
        has_afk_changed = (afk != self.current_afk)
        has_exceeded_max_block = (
            self.block_start_time is not None
            and (now - self.block_start_time).total_seconds() >= self.max_block_sec
        )

        if has_context_switched or has_afk_changed or has_exceeded_max_block:
            # Sluit vorig blok af en verstuur
            self.flush_current_block()

            # Start nieuw blok
            self.current_app = app_name
            self.current_title = title
            self.current_afk = afk
            self.block_start_time = now

    def start(self) -> None:
        """
        Start de continue logging loop.
        Blijft draaien zolang self.is_running True is.
        Kan netjes gestopt worden via self.stop() of KeyboardInterrupt.
        """
        print(f"[LOGGER] Gestart voor device '{self.device_id}'.")
        self.is_running = True
        try:
            while self.is_running:
                self.step()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """
        Stopt de actieve logging loop netjes en slaat het huidige blok op.
        Geschikt voor CLI (Ctrl+C), GUI-events (stop-knop of sluiten venster) en mobiele lifecycle triggers.
        """
        if not self.is_running:
            return
        print("[LOGGER] Stop-signaal ontvangen. Huidige sessie opslaan...")
        self.is_running = False
        self.flush_current_block()
        print("[LOGGER] Succesvol gestopt.")


if __name__ == "__main__":
    # Test instantie (werkt ook met dummy token in offline buffer modus)
    logger = PCLogger(
        device_id="pc-01",
        token="test_token",
        api_url="http://127.0.0.1:8000",
        poll_interval=1.0,
        afk_threshold_sec=5,
    )

    print("Logger testcyclus draaien (2 seconden)...")
    for _ in range(2):
        logger.step()
        time.sleep(1)
    logger.flush_current_block()
    print("Testcyclus succesvol voltooid! Gebufferde items:", len(logger.offline_queue))
