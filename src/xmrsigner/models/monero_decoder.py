from xmrsigner.models.base_decoder import BaseSingleFrameQrDecoder
from xmrsigner.models.qr_type import QRType
from monero.address import address as monero_address
from monero.address import Address

from urllib.parse import urlparse, parse_qs
from re import search
from typing import List, Dict, Optional, Union


class MoneroAddressQrDecoder(BaseSingleFrameQrDecoder):
    """
        Decodes single frame representing a monero address
    """

    def __init__(self):
        super().__init__()
        self.address: Optional[str] = None
        self.address_type: Optional[str] = None

    def add(self, segment, qr_type=QRType.MONERO_ADDRESS):
        r = search(r'\b[1-9A-HJ-NP-Za-km-z]{95}\b|[1-9A-HJ-NP-Za-km-z]{106}', segment)
        if r != None:
            try:
                a = monero_address(r.group(1))
                self.address_type = a.net
                self.address = str(a)
                self.complete = True
                self.collected_segments = 1
                return DecodeQRStatus.COMPLETE
            except:
                pass
        return DecodeQRStatus.INVALID

    def get_address(self):
        if self.address != None:
            return self.address
        return None

    def get_address_type(self):
        if self.address != None:
            if self.address_type != None:
                return self.address_type
            else:
                return "Unknown"
        return None


class MoneroWalletQrDecoder(BaseSingleFrameQrDecoder):
    """
        Decodes single frame representing a monero wallet
    """

    def __init__(self):
        super().__init__()
        self.address: Optional[str] = None
        self.view_key: Optional[str] = None
        self.spend_key: Optional[str] = None
        self.height: int = 0

    def parse_monero_wallet_uri(self, uri: str):
        parsed_uri = urlparse(uri)
        query_params = parse_qs(parsed_uri.query)

        address = parsed_uri.path.split(':')[-1]
        view_key = query_params.get('view_key', [''])[0]
        spend_key = query_params.get('spend_key', [''])[0]
        height = query_params.get('height', [''])[0]

        return address, view_key, spend_key, height

    def add(self, segment, qr_type=QRType.MONERO_WALLET):
        address, view_key, spend_key, height = self.parse_monero_wallet_uri(segment)
        if address != None:
            try:
                a: Address = monero_address(address)
                self.address_type = a.net
                self.address = str(a)
                self.view_key = view_key
                self.spend_key = spend_key
                self.height = int(height or 0)
                self.complete = True
                self.collected_segments = 1
                return DecodeQRStatus.COMPLETE
            except:
                pass
        return DecodeQRStatus.INVALID

    @property
    def is_valid(self):
        return self.address is not None and self.view_key is not None

    @property
    def is_view_only(self):
        return self.spend_key is None

    @property
    def has_height(self):
        return self.height != 0

    def get_data(self) -> Union[Dict, List, str, bytes]:
        return {
            'address': self.address,
            'view_key': self.view_key,
            'spend_key': self.spend_key,
            'height': self.height
            }

    @staticmethod
    def is_monero_address(s: str) -> bool:
        if s.startswith('monero:'):
            s = s[7:]
        try:
            monero_address(s)
            return True
        except:
            return False