import random
import time

from binascii import hexlify
from typing import List
from math import ceil

from xmrsigner.helpers.network import Network
from xmrsigner.controller import Controller
from xmrsigner.gui.components import (
    GUIConstants,
    FontAwesomeIconConstants,
    IconConstants
)
from xmrsigner.gui.button_data import ButtonData, FingerprintButtonData
from xmrsigner.gui.screens import (
    RET_CODE__BACK_BUTTON,
    ButtonListScreen,
    WarningScreen,
    DireWarningScreen,
    seed_screens
)
from xmrsigner.gui.screens.screen import (
    LargeIconStatusScreen,
    QRDisplayScreen
)
from xmrsigner.gui.screens.monero_screens import DateOrBlockHeightScreen
from xmrsigner.models.decode_qr import DecodeQR
from xmrsigner.models.seed_encoder import SeedQrEncoder, CompactSeedQrEncoder
from xmrsigner.models.tx_parser import TxParser
from xmrsigner.models.qr_type import QRType
from xmrsigner.models.seed import InvalidSeedException, Seed, SeedType
from xmrsigner.models.polyseed import PolyseedSeed
from xmrsigner.models.settings import Settings, SettingsConstants
from xmrsigner.models.settings_definition import SettingsDefinition
from xmrsigner.models.threads import BaseThread, ThreadsafeCounter
from xmrsigner.views.wallet_views import (
    WalletViewKeyQRView,
    WalletViewKeyJsonQRView,
    LoadWalletView,
    ImportOutputsView,
    ExportKeyImagesView
)
from xmrsigner.views.view import (
    NotYetImplementedView,
    OptionDisabledView,
    View,
    Destination,
    BackStackView,
    MainMenuView
)


class SeedsMenuView(View):

    LOAD = 'Load a seed'

    def __init__(self):
        super().__init__()

    def run(self):
        if len(self.controller.jar.seeds) < 1:
            # Nothing to do here unless we have a seed loaded
            return Destination(LoadSeedView, clear_history=True)
        button_data = []
        for seed in self.controller.jar.seeds:
            button_data.append(
                    FingerprintButtonData(
                    seed.fingerprint,
                    seed.has_passphrase,
                    isinstance(seed, PolyseedSeed),
                    seed.is_my_monero
                )
            )
        button_data.append('Load a seed')
        selected_menu_num = self.run_screen(
            ButtonListScreen,
            title='In-Memory Seeds',
            is_button_text_centered=False,
            button_data=button_data
        )
        if len(self.controller.jar.seeds) > 0 and selected_menu_num < len(self.controller.jar.seeds):
            return Destination(SeedOptionsView, view_args={'seed_num': selected_menu_num})
        if selected_menu_num == len(self.controller.jar.seeds):
            return Destination(LoadSeedView)
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)


"""
****************************************************************************
    Loading seeds, passphrases, etc
****************************************************************************
"""
class LoadSeedView(View):

    SEED_QR = ButtonData('Scan a SeedQR').with_icon(IconConstants.QRCODE)
    TYPE_13WORD = ButtonData('Enter 13-word seed').with_icon(FontAwesomeIconConstants.KEYBOARD)
    TYPE_25WORD = ButtonData('Enter 25-word seed').with_icon(FontAwesomeIconConstants.KEYBOARD)
    TYPE_POLYSEED = ButtonData('Enter Polyseed').with_icon(FontAwesomeIconConstants.KEYBOARD)
    CREATE = ButtonData('Create a seed').with_icon(IconConstants.PLUS)

    def run(self):
        button_data=[
            self.SEED_QR,
            self.TYPE_13WORD,
            self.TYPE_25WORD,
            self.TYPE_POLYSEED,
            self.CREATE,
        ]
        selected_menu_num = self.run_screen(
            ButtonListScreen,
            title='Load A Seed',
            is_button_text_centered=False,
            button_data=button_data
        )
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        if button_data[selected_menu_num] == self.SEED_QR:
            from xmrsigner.views.scan_views import ScanSeedQRView
            return Destination(ScanSeedQRView)
        if button_data[selected_menu_num] == self.TYPE_13WORD:
            self.controller.jar.init_pending_mnemonic(num_words=13)
            return Destination(SeedMnemonicEntryView)
        if button_data[selected_menu_num] == self.TYPE_25WORD:
            self.controller.jar.init_pending_mnemonic(num_words=25)
            return Destination(SeedMnemonicEntryView)
        if button_data[selected_menu_num] == self.TYPE_POLYSEED:
            self.controller.jar.init_pending_mnemonic(num_words=16)
            return Destination(PolyseedMnemonicEntryView)
        if button_data[selected_menu_num] == self.CREATE:
            from .tools_views import ToolsMenuView
            return Destination(ToolsMenuView)


class SeedMnemonicEntryView(View):

    def __init__(self, cur_word_index: int = 0, is_calc_final_word: bool=False):
        super().__init__()
        self.cur_word_index = cur_word_index
        self.cur_word = self.controller.jar.get_pending_mnemonic_word(cur_word_index)
        self.is_calc_final_word = is_calc_final_word

    def run(self):
        ret = self.run_screen(
            seed_screens.SeedMnemonicEntryScreen,
            title=f'Seed Word #{self.cur_word_index + 1}',  # Human-readable 1-indexing!
            initial_letters=list(self.cur_word) if self.cur_word else ['a'],
            wordlist=Seed.get_wordlist(wordlist_language_code=self.settings.get_value(SettingsConstants.SETTING__MONERO_WORDLIST_LANGUAGE)),
        )
        if ret == RET_CODE__BACK_BUTTON:
            if self.cur_word_index > 0:
                return Destination(BackStackView)
            self.controller.jar.discard_pending_mnemonic()
            return Destination(MainMenuView)
        # ret will be our new mnemonic word
        self.controller.jar.update_pending_mnemonic(ret, self.cur_word_index)
        if self.is_calc_final_word and self.cur_word_index == self.controller.jar.pending_mnemonic_length - 2:
            # Time to calculate the last word. User must decide how they want to specify
            # the last bits of entropy for the final word.
            from xmrsigner.views.tools_views import ToolsCalcFinalWordShowFinalWordView
            return Destination(ToolsCalcFinalWordShowFinalWordView, view_args=dict(coin_flips="0" * 7))
        if self.is_calc_final_word and self.cur_word_index == self.controller.jar.pending_mnemonic_length - 1:
            # Time to calculate the last word. User must either select a final word to
            # contribute entropy to the checksum word OR we assume 0 ("abandon").
            from xmrsigner.views.tools_views import ToolsCalcFinalWordShowFinalWordView
            return Destination(ToolsCalcFinalWordShowFinalWordView)
        if self.cur_word_index < self.controller.jar.pending_mnemonic_length - 1:
            return Destination(
                SeedMnemonicEntryView,
                view_args={
                    "cur_word_index": self.cur_word_index + 1,
                    "is_calc_final_word": self.is_calc_final_word
                }
            )
        # Attempt to finalize the mnemonic
        try:
            self.controller.jar.convert_pending_mnemonic_to_pending_seed()
        except InvalidSeedException:
            return Destination(SeedMnemonicInvalidView)
        return Destination(SeedFinalizeView)


class PolyseedMnemonicEntryView(SeedMnemonicEntryView):

    def __init__(self, cur_word_index: int = 0):
        super().__init__(cur_word_index, False)

    def run(self):
        ret = self.run_screen(
            seed_screens.SeedMnemonicEntryScreen,
            title=f"Polyseed Word #{self.cur_word_index + 1}",  # Human-readable 1-indexing!
            initial_letters=list(self.cur_word) if self.cur_word else ["a"],
            wordlist=PolyseedSeed.get_wordlist(wordlist_language_code=self.settings.get_value(SettingsConstants.SETTING__POLYSEED_WORDLIST_LANGUAGE)),
        )
        if ret == RET_CODE__BACK_BUTTON:
            if self.cur_word_index > 0:
                return Destination(BackStackView)
            self.controller.jar.discard_pending_mnemonic()
            return Destination(MainMenuView)
        # ret will be our new mnemonic word
        self.controller.jar.update_pending_mnemonic(ret, self.cur_word_index)
        if self.cur_word_index < self.controller.jar.pending_mnemonic_length - 1:
            return Destination(
                PolyseedMnemonicEntryView,
                view_args={
                    "cur_word_index": self.cur_word_index + 1
                }
            )
        # Attempt to finalize the mnemonic
        try:
            self.controller.jar.convert_pending_mnemonic_to_pending_polyseed()
        except InvalidSeedException as e:
            print(e) # TODO: 2024-10-24, remove, debugging only
            print(f'pending seed: {' '.join(self.controller.jar.pending_mnemonic)}')  # TODO: remove, debugging only
            return Destination(SeedMnemonicInvalidView, view_args={'polyseed': True})
        return Destination(SeedFinalizeView)


class SeedMnemonicInvalidView(View):

    EDIT = ButtonData('Review & Edit')
    DISCARD = ButtonData.DISCARD

    def __init__(self, polyseed: bool = False):
        super().__init__()
        self.mnemonic: List[str] = self.controller.jar.pending_mnemonic
        self.polyseed = polyseed

    def run(self):
        button_data = [self.EDIT, self.DISCARD]
        selected_menu_num = self.run_screen(
            WarningScreen,
            title="Invalid Mnemonic!",
            status_headline=None,
            text=f"Checksum failure; not a valid seed phrase.",
            show_back_button=False,
            button_data=button_data,
        )
        if button_data[selected_menu_num] == self.EDIT:
            return Destination(
                PolyseedMnemonicEntryView if self.polyseed else SeedMnemonicEntryView,
                view_args={"cur_word_index": 0}
            )
        if button_data[selected_menu_num] == self.DISCARD:
            self.controller.jar.discard_pending_mnemonic()
            return Destination(MainMenuView)


class SeedFinalizeView(View):

    FINALIZE = ButtonData('Done')
    PASSPHRASE = ButtonData('Add Passphrase').with_icon(FontAwesomeIconConstants.LOCK)

    def __init__(self):
        super().__init__()
        self.seed = self.controller.jar.get_pending_seed()
        self.polyseed = isinstance(self.seed, PolyseedSeed)

    def run(self):
        networks = Network.get_list(self.settings.get_value(SettingsConstants.SETTING__NETWORKS))
        if len(networks) == 1 and self.seed.network != str(networks[0]):
            self.seed.change_network(str(networks[0])) 
        if len(networks) > 1:
            ret = self.run_screen(
                ButtonListScreen,
                title='Choose Network',
                button_data=[ButtonData(str(network).capitalize()) for network in networks]
            )
            if ret == RET_CODE__BACK_BUTTON:
                return Destination(BackStackView)
            network = networks[ret]
            if self.seed.network != str(network):
                self.seed.change_network(str(network)) 
        if not self.polyseed:
            ret = self.run_screen(DateOrBlockHeightScreen)
            if ret == RET_CODE__BACK_BUTTON:
                return Destination(BackStackView)
            if type(ret) == str:
                self.seed.height = int(ret)
        button_data = []
        button_data.append(self.FINALIZE)
        if (
                not self.polyseed
                and self.settings.get_value(SettingsConstants.SETTING__MONERO_SEED_PASSPHRASE) == SettingsConstants.OPTION__ENABLED
            ) or (
                self.polyseed
                and self.settings.get_value(SettingsConstants.SETTING__POLYSEED_PASSPHRASE) == SettingsConstants.OPTION__ENABLED
            ):
            button_data.append(self.PASSPHRASE)
        selected_menu_num = self.run_screen(
            seed_screens.SeedFinalizeScreen,
            fingerprint=self.seed.fingerprint,
            polyseed=self.polyseed,
            button_data=button_data,
        )
        if button_data[selected_menu_num] == self.FINALIZE:
            seed_num = self.controller.jar.finalize_pending_seed()
            return Destination(SeedOptionsView, view_args={'seed_num': seed_num}, clear_history=True)
        if button_data[selected_menu_num] == self.PASSPHRASE:
            return Destination(SeedAddPassphraseView)


class SeedAddPassphraseView(View):

    def __init__(self):
        super().__init__()
        self.seed = self.controller.jar.get_pending_seed()

    def run(self):
        ret = self.run_screen(seed_screens.SeedAddPassphraseScreen, passphrase=self.seed.passphrase_str)
        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        # The new passphrase will be the return value; it might be empty.
        self.seed.set_passphrase(ret)
        if len(self.seed.passphrase) > 0:
            return Destination(SeedReviewPassphraseView)
        return Destination(SeedFinalizeView)


class SeedReviewPassphraseView(View):
    '''
    Display the completed passphrase back to the user.
    '''

    EDIT = ButtonData('Edit passphrase')
    DONE = ButtonData('Done')

    def __init__(self):
        super().__init__()
        self.seed = self.controller.jar.get_pending_seed()

    def run(self):
        # Get the before/after fingerprints
        network = self.settings.get_value(SettingsConstants.SETTING__NETWORKS)[0]  # TODO: 2024-06-26, solve multi network issue
        passphrase = self.seed.passphrase
        fingerprint_with = self.seed.fingerprint
        self.seed.set_passphrase(None)
        fingerprint_without = self.seed.fingerprint
        self.seed.set_passphrase(passphrase)
        button_data = [self.EDIT, self.DONE]
        # Because we have an explicit "Edit" button, we disable "BACK" to keep the
        # routing options sane.
        selected_menu_num = self.run_screen(
            seed_screens.SeedReviewPassphraseScreen,
            fingerprint_without=fingerprint_without,
            fingerprint_with=fingerprint_with,
            passphrase=self.seed.passphrase,
            polyseed=isinstance(self.seed, PolyseedSeed),
            my_monero=self.seed.is_my_monero,
            button_data=button_data,
            show_back_button=False,
        )
        if button_data[selected_menu_num] == self.EDIT:
            return Destination(SeedAddPassphraseView)
        if button_data[selected_menu_num] == self.DONE:
            seed_num = self.controller.jar.finalize_pending_seed()
            return Destination(SeedOptionsView, view_args={"seed_num": seed_num}, clear_history=True)
            
            
class SeedDiscardView(View):

    KEEP = ButtonData('Keep Seed')
    DISCARD = ButtonData.DISCARD

    def __init__(self, seed_num: int = None):
        super().__init__()
        self.seed_num = seed_num
        if self.seed_num is not None:
            self.seed = self.controller.get_seed(self.seed_num)
        else:
            self.seed = self.controller.jar.pending_seed

    def run(self):
        button_data = [self.KEEP, self.DISCARD]
        selected_menu_num = self.run_screen(
            WarningScreen,
            title='Discard Seed?',
            status_headline=None,
            text=f'Wipe seed {self.seed.fingerprint} from the device?',
            show_back_button=False,
            button_data=button_data,
        )
        if button_data[selected_menu_num] == self.KEEP:
            # Use skip_current_view=True to prevent BACK from landing on this warning screen
            if self.seed_num is not None:
                return Destination(SeedOptionsView, view_args={'seed_num': self.seed_num}, skip_current_view=True)
            return Destination(SeedFinalizeView, skip_current_view=True)
        if button_data[selected_menu_num] == self.DISCARD:
            if self.seed_num is not None:
                seed = self.controller.get_seed(self.seed_num)
                if self.controller.get_wallet_seed(seed.network) == seed:
                    try:
                        self.controller.clear_wallet_seed(seed.network)
                        self.controller.clear_wallet(seed.network)
                        self.controller.wallet_rpc_manager.close_wallet(seed.network)
                        self.controller.wallet_rpc_manager.purge_wallet(seed.fingerprint)
                    except Exception as e:
                        print(f'Unexcpected issue on purging wallet for seed: {seed.fingerprint}: {e}')
                self.controller.discard_seed(self.seed_num)
            else:
                self.controller.jar.clear_pending_seed()
            return Destination(MainMenuView, clear_history=True)


class SeedOptionsView(View):
    '''
    Views for actions on individual seeds:
    '''

    SCAN = ButtonData('Scan for Seed').with_icon(IconConstants.SCAN)
    EXPORT_KEY_IMAGES = ButtonData('Export Key Images').with_icon(IconConstants.QRCODE)
    EXPLORER = ButtonData('Address Explorer')
    VIEW_ONLY_WALLET = ButtonData('View only Wallet').with_icon(IconConstants.QRCODE)
    VIEW_ONLY_WALLET_JSON = ButtonData('View only Wallet (json)').with_icon(IconConstants.QRCODE)
    LOAD_WALLET = ButtonData('Load into Wallet').with_icon(FontAwesomeIconConstants.WALLET)
    PURGE_WALLET = ButtonData('Purge from Wallet').with_icon(FontAwesomeIconConstants.TRASH_CAN)
    BACKUP = ButtonData('Backup Seed').with_icon(FontAwesomeIconConstants.VAULT).with_right_icon(IconConstants.CHEVRON_RIGHT)
    CONVERT_POOLYSEED = ButtonData('To Monero seed').with_icon(IconConstants.CHEVRON_RIGHT)
    DISCARD = ButtonData.DISCARD.with_icon(FontAwesomeIconConstants.TRASH_CAN).with_icon_color(GUIConstants.RED)

    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num
        self.seed = self.controller.get_seed(self.seed_num)

    def run(self):
        from xmrsigner.views.monero_views import OverviewView
        if self.controller.transaction:
            if TxParser.has_matching_input_fingerprint(self.controller.transaction, self.seed, network=self.seed.network):
                if self.controller.resume_main_flow and self.controller.resume_main_flow == Controller.FLOW__TX:
                    # Re-route us directly back to the start of the Tx flow 
                    self.controller.resume_main_flow = None
                    self.controller.transaction_seed = self.seed
                    return Destination(OverviewView, skip_current_view=True)
        button_data = []
        button_data.append(self.SCAN)
        button_data.append(self.EXPORT_KEY_IMAGES)
        if len(self.settings.get_value(SettingsConstants.SETTING__VIEW_WALLET_QR_FORMAT)) > 1:
            self.VIEW_ONLY_WALLET.with_right_icon(IconConstants.CHEVRON_RIGHT)
        button_data.append(self.VIEW_ONLY_WALLET)
        # button_data.append(self.VIEW_ONLY_WALLET_JSON)  # TODO: 2024-08-26, finish implementation
        if self.controller.get_wallet_seed(self.seed.network) != self.seed:
            button_data.append(self.LOAD_WALLET)
        else:
            # button_data.append(self.PURGE_WALLET) # TODO: 2024-08-09, implement
            pass
        button_data.append(self.BACKUP)
        if isinstance(self.seed, PolyseedSeed):
            button_data.append(self.CONVERT_POOLYSEED)
        button_data.append(self.DISCARD)

        selected_menu_num = self.run_screen(
            seed_screens.SeedOptionsScreen,
            button_data=button_data,
            fingerprint=self.seed.fingerprint,
            polyseed=isinstance(self.seed, PolyseedSeed),
            my_monero=self.seed.is_my_monero,
            has_passphrase=self.seed.passphrase is not None
        )
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            # Force BACK to always return to the Main Menu if in a flow
            return Destination(BackStackView if self.controller.resume_main_flow is None else MainMenuView)
        if button_data[selected_menu_num] == self.SCAN:
            from xmrsigner.views.scan_views import ScanUR2View
            return Destination(ScanUR2View)
        if button_data[selected_menu_num] == self.BACKUP:
            return Destination(SeedBackupView, view_args={"seed_num": self.seed_num})
        if button_data[selected_menu_num] == self.CONVERT_POOLYSEED:
            if isinstance(self.seed, PolyseedSeed):
                self.controller.replace_seed(self.seed_num, self.seed.to_monero_seed(None))
                return Destination(SeedOptionsView, view_args={"seed_num": self.seed_num}, skip_current_view=True)
            self.run_screen(
                DireWarningScreen,
                title='Not a Polyseed',
                status_headline='Error!',
                text="Can't convert to monero seed!",
                show_back_button=False,
                button_data=['OK'],
            ).display()
            return Destination(BackStackView, skip_current_view=True)
        if button_data[selected_menu_num] == self.EXPORT_KEY_IMAGES:
            return Destination(ExportKeyImagesView, view_args={'network': self.seed.network, 'seed_num': self.seed_num})
        if button_data[selected_menu_num] == self.VIEW_ONLY_WALLET:
            return Destination(WalletViewKeyQRView, view_args={'seed_num': self.seed_num})
        if button_data[selected_menu_num] == self.VIEW_ONLY_WALLET_JSON:
            return Destination(WalletViewKeyJsonQRView, view_args={'seed_num': self.seed_num})
        if button_data[selected_menu_num] == self.LOAD_WALLET:
            return Destination(LoadWalletView, view_args={'seed_num': self.seed_num})
        if button_data[selected_menu_num] == self.PURGE_WALLET:
            # return Destination(PurgeWalletView, view_args={'seed_num': self.seed_num})
            pass
        if button_data[selected_menu_num] == self.DISCARD:
            return Destination(SeedDiscardView, view_args={"seed_num": self.seed_num})


class SeedBackupView(View):
    
    def __init__(self, seed_num):
        super().__init__()
        self.seed_num = seed_num
        self.seed = self.controller.get_seed(self.seed_num)

    def run(self):
        VIEW_WORDS = ButtonData('View Seed Words').with_icon(FontAwesomeIconConstants.LIST)
        EXPORT_SEEDQR = ButtonData('Export as SeedQR').with_icon(FontAwesomeIconConstants.PEN)
        button_data = [VIEW_WORDS, EXPORT_SEEDQR]
        selected_menu_num = ButtonListScreen(
            title='Backup Seed',
            button_data=button_data,
            is_bottom_list=True,
        ).display()
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        if button_data[selected_menu_num] == VIEW_WORDS:
            return Destination(SeedWordsWarningView, view_args={'seed_num': self.seed_num})
        if button_data[selected_menu_num] == EXPORT_SEEDQR:
            return Destination(SeedTranscribeSeedQRFormatView, view_args={'seed_num': self.seed_num})


"""****************************************************************************
    View Seed Words flow
****************************************************************************"""
class SeedWordsWarningView(View):

    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num

    def run(self):
        destination = Destination(
            SeedWordsView,
            view_args={'seed_num': self.seed_num, 'page_index': 0},
            skip_current_view=True,  # Prevent going BACK to WarningViews
        )
        if self.settings.get_value(SettingsConstants.SETTING__DIRE_WARNINGS) == SettingsConstants.OPTION__DISABLED:
            # Forward straight to showing the words
            return destination
        selected_menu_num = DireWarningScreen(
            text='''You must keep your seed words private & away from all online devices.''',
        ).display()
        if selected_menu_num == 0:
            # User clicked 'I Understand'
            return destination
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)


class SeedWordsView(View):

    def __init__(self, seed_num: int, page_index: int = 0):
        super().__init__()
        self.seed_num = seed_num
        if self.seed_num is None:
            self.seed = self.controller.jar.get_pending_seed()
        else:
            self.seed = self.controller.get_seed(self.seed_num)
        self.page_index = page_index
        self.num_pages=int(ceil(len(self.seed.mnemonic_list)/4))

    def run(self):
        NEXT = ButtonData.NEXT
        DONE = ButtonData.DONE
        # Slice the mnemonic to our current 4-word section
        words_per_page = 4
        mnemonic = self.seed.mnemonic_display_list
        words = mnemonic[self.page_index * words_per_page:(self.page_index + 1) * words_per_page]
        button_data = []
        if self.page_index < self.num_pages - 1 or self.seed_num is None:
            button_data.append(NEXT)
        else:
            button_data.append(DONE)
        selected_menu_num = seed_screens.SeedWordsScreen(
            title=f"Seed Words: {self.page_index+1}/{self.num_pages}",
            words=words,
            page_index=self.page_index,
            num_pages=self.num_pages,
            button_data=button_data,
            words_per_page = words_per_page,
        ).display()
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        if button_data[selected_menu_num] == NEXT:
            if self.seed_num is None and self.page_index == self.num_pages - 1:
                return Destination(SeedWordsBackupTestPromptView, view_args=dict(seed_num=self.seed_num))
            return Destination(SeedWordsView, view_args=dict(seed_num=self.seed_num, page_index=self.page_index + 1))
        if button_data[selected_menu_num] == DONE:
            # Must clear history to avoid BACK button returning to private info
            return Destination(SeedWordsBackupTestPromptView, view_args=dict(seed_num=self.seed_num))


"""****************************************************************************
    Seed Words Backup Test
****************************************************************************"""
class SeedWordsBackupTestPromptView(View):

    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num

    def run(self):
        VERIFY = ButtonData('Verify')
        SKIP = ButtonData('Skip')
        button_data = [VERIFY, SKIP]
        selected_menu_num = seed_screens.SeedWordsBackupTestPromptScreen(
            button_data=button_data,
        ).display()
        if button_data[selected_menu_num] == VERIFY:
            return Destination(SeedWordsBackupTestView, view_args=dict(seed_num=self.seed_num))
        if button_data[selected_menu_num] == SKIP:
            if self.seed_num is not None:
                return Destination(SeedOptionsView, view_args=dict(seed_num=self.seed_num))
            return Destination(SeedFinalizeView)


class SeedWordsBackupTestView(View):

    def __init__(self, seed_num: int, confirmed_list: List[bool] = None, cur_index: int = None):
        super().__init__()
        self.seed_num = seed_num
        if self.seed_num is None:
            self.seed = self.controller.jar.get_pending_seed()
        else:
            self.seed = self.controller.get_seed(self.seed_num)
        self.mnemonic_list = self.seed.mnemonic_display_list
        self.confirmed_list = confirmed_list
        if not self.confirmed_list:
            self.confirmed_list = []
        self.cur_index = cur_index

    def run(self):
        if self.cur_index is None:
            self.cur_index = int(random.random() * len(self.mnemonic_list))
            while self.cur_index in self.confirmed_list:
                self.cur_index = int(random.random() * len(self.mnemonic_list))
        real_word = self.mnemonic_list[self.cur_index]
        button_data = [real_word]
        while len(button_data) < 4:
            new_word = random.choice(self.seed.get_wordlist(self.seed.wordlist_language_code))
            if new_word not in button_data:
                button_data.append(new_word)
        random.shuffle(button_data)
        selected_menu_num = ButtonListScreen(
            title=f"Verify Word #{self.cur_index + 1}",
            show_back_button=False,
            button_data=button_data,
            is_bottom_list=True,
            is_button_text_centered=True,
        ).display()
        if button_data[selected_menu_num] == real_word:
            self.confirmed_list.append(self.cur_index)
            if len(self.confirmed_list) == len(self.mnemonic_list):
                # Successfully confirmed the full mnemonic!
                return Destination(SeedWordsBackupTestSuccessView, view_args=dict(seed_num=self.seed_num))
            # Continue testing the remaining words
            return Destination(SeedWordsBackupTestView, view_args=dict(seed_num=self.seed_num, confirmed_list=self.confirmed_list))
        else:
            # Picked the WRONG WORD!
            return Destination(
                SeedWordsBackupTestMistakeView,
                view_args=dict(
                    seed_num=self.seed_num,
                    cur_index=self.cur_index,
                    wrong_word=button_data[selected_menu_num],
                    confirmed_list=self.confirmed_list,
                )
            )


class SeedWordsBackupTestMistakeView(View):
    
    def __init__(self, seed_num: int, cur_index: int, wrong_word: str, confirmed_list: List[bool] = None):
        super().__init__()
        self.seed_num = seed_num
        self.cur_index = cur_index
        self.wrong_word = wrong_word
        self.confirmed_list = confirmed_list

    def run(self):
        REVIEW = ButtonData('Review Seed Words')
        RETRY = ButtonData('Try Again')
        button_data = [REVIEW, RETRY]
        selected_menu_num = DireWarningScreen(
            title='Verification Error',
            show_back_button=False,
            status_headline=f'Wrong Word!',
            text=f'Word #{self.cur_index + 1} is not "{self.wrong_word}"!',
            button_data=button_data,
        ).display()
        if button_data[selected_menu_num] == REVIEW:
            return Destination(SeedWordsView, view_args=dict(seed_num=self.seed_num))
        if button_data[selected_menu_num] == RETRY:
            return Destination(SeedWordsBackupTestView, view_args=dict(seed_num=self.seed_num, confirmed_list=self.confirmed_list, cur_index=self.cur_index))


class SeedWordsBackupTestSuccessView(View):

    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num
    
    def run(self):
        LargeIconStatusScreen(
            title='Backup Verified',
            show_back_button=False,
            status_headline='Success!',
            text='All mnemonic backup words were successfully verified!',
            button_data=[ButtonData.OK]
        ).display()
        if self.seed_num is not None:
            return Destination(SeedOptionsView, view_args=dict(seed_num=self.seed_num), clear_history=True)
        else:
            return Destination(SeedFinalizeView)


"""****************************************************************************
    Export as SeedQR
****************************************************************************"""
class SeedTranscribeSeedQRFormatView(View):

    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num

    def run(self):
        seed: Seed = self.controller.get_seed(self.seed_num)
        num_modules_standard = {
                SeedType.Monero: 29,
                SeedType.MyMonero: 25,
                SeedType.Polyseed: 25
            }[seed.type]
        num_modules_compact = {
                SeedType.Monero: 25,
                SeedType.MyMonero: 21,
                SeedType.Polyseed: 25
            }[seed.type]
        STANDARD = ButtonData(f'Standard: {num_modules_standard}x{num_modules_standard}')
        COMPACT = ButtonData(f'Compact: {num_modules_compact}x{num_modules_compact}')
        if self.settings.get_value(SettingsConstants.SETTING__COMPACT_SEEDQR) != SettingsConstants.OPTION__ENABLED:
            # Only configured for standard SeedQR
            return Destination(
                SeedTranscribeSeedQRWarningView,
                view_args={
                    'seed_num': self.seed_num,
                    'seedqr_format': QRType.SEED__SEEDQR,
                    'num_modules': num_modules_standard,
                },
                skip_current_view=True,
            )
        button_data = [STANDARD, COMPACT]
        selected_menu_num = seed_screens.SeedTranscribeSeedQRFormatScreen(
            title='SeedQR Format',
            seed_type=seed.type,
            button_data=button_data,
        ).display()
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        if button_data[selected_menu_num] == STANDARD:
            seedqr_format = QRType.SEED__SEEDQR
            num_modules = num_modules_standard
        else:
            seedqr_format = QRType.SEED__COMPACTSEEDQR
            num_modules = num_modules_compact
        return Destination(
            SeedTranscribeSeedQRWarningView,
                view_args={
                    'seed_num': self.seed_num,
                    'seedqr_format': seedqr_format,
                    'num_modules': num_modules,
                }
            )


class SeedTranscribeSeedQRWarningView(View):

    def __init__(self, seed_num: int, seedqr_format: str = QRType.SEED__SEEDQR, num_modules: int = 29):
        super().__init__()
        self.seed_num = seed_num
        self.seedqr_format = seedqr_format
        self.num_modules = num_modules

    def run(self):
        destination = Destination(
            SeedTranscribeSeedQRWholeQRView,
            view_args={
                'seed_num': self.seed_num,
                'seedqr_format': self.seedqr_format,
                'num_modules': self.num_modules,
            },
            skip_current_view=True,  # Prevent going BACK to WarningViews
        )
        if self.settings.get_value(SettingsConstants.SETTING__DIRE_WARNINGS) == SettingsConstants.OPTION__DISABLED:
            # Forward straight to transcribing the SeedQR
            return destination
        selected_menu_num = DireWarningScreen(
                status_headline='SeedQR is your private key!',
            text='''Never photograph it or scan it into an online device.''',
        ).display()
        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        # User clicked 'I Understand'
        return destination


class SeedTranscribeSeedQRWholeQRView(View):
    
    def __init__(self, seed_num: int, seedqr_format: str, num_modules: int):
        super().__init__()
        self.seed_num = seed_num
        self.seedqr_format = seedqr_format
        self.num_modules = num_modules
        self.seed = self.controller.get_seed(seed_num)

    def run(self):
        e = SeedQrEncoder(self.seed.mnemonic_list, self.seed.wordlist) if self.seedqr_format == QRType.SEED__SEEDQR else CompactSeedQrEncoder(self.seed.mnemonic_list, self.seed.wordlist)
        ret = seed_screens.SeedTranscribeSeedQRWholeQRScreen(
            qr_data=e.next_part(),
            num_modules=self.num_modules,
        ).display()
        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        return Destination(
            SeedTranscribeSeedQRZoomedInView,
            view_args={
                'seed_num': self.seed_num,
                'seedqr_format': self.seedqr_format
            }
        )


class SeedTranscribeSeedQRZoomedInView(View):

    def __init__(self, seed_num: int, seedqr_format: str):
        super().__init__()
        self.seed_num = seed_num
        self.seedqr_format = seedqr_format
        self.seed = self.controller.get_seed(seed_num)
    
    def run(self):
        if self.seedqr_format == QRType.SEED__SEEDQR:
            num_modules = 29 if (len(self.mnemonic_list) * 4) > 77 else 25  # Version 1 can fit 77 numeric digits into 25x25 and up to 127 numeric digits into 29x29
        elif self.seedqr_format == QRType.SEED__COMPACTSEEDQR:
            num_modules = 25 if ceil(len(self.mnemonic_list) * 11 / 8) > 32 else 21  # Version 1 can fit 17 bytes into 21x21 and up to 32 bytes into 25x25
        e = SeedQrEncoder(self.seed.mnemonic_list, self.seed.wordlist) if self.seedqr_format == QRType.SEED__SEEDQR else CompactSeedQrEncoder(self.seed.mnemonic_list, self.seed.wordlist)
        seed_screens.SeedTranscribeSeedQRZoomedInScreen(
            qr_data=e.next_part(),
            num_modules=num_modules,
        ).display()
        return Destination(SeedTranscribeSeedQRConfirmQRPromptView, view_args={'seed_num': self.seed_num})


class SeedTranscribeSeedQRConfirmQRPromptView(View):
    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num
        self.seed = self.controller.get_seed(seed_num)

    def run(self):
        SCAN = ButtonData('Confirm SeedQR').with_icon(FontAwesomeIconConstants.QRCODE)
        DONE = ButtonData.DONE
        button_data = [SCAN, DONE]
        selected_menu_option = seed_screens.SeedTranscribeSeedQRConfirmQRPromptScreen(
            title='Confirm SeedQR?',
            button_data=button_data,
        ).display()
        if selected_menu_option == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        if button_data[selected_menu_option] == SCAN:
            return Destination(SeedTranscribeSeedQRConfirmScanView, view_args={'seed_num': self.seed_num})
        if button_data[selected_menu_option] == DONE:
            return Destination(SeedOptionsView, view_args={'seed_num': self.seed_num}, clear_history=True)


class SeedTranscribeSeedQRConfirmScanView(View):
    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num
        self.seed = self.controller.get_seed(seed_num)

    def run(self):
        from xmrsigner.gui.screens.scan_screens import ScanScreen
        # Run the live preview and QR code capture process
        wordlist_language_code = self.settings.get_value(SettingsConstants.SETTING__MONERO_WORDLIST_LANGUAGE if not isinstance(self.seed, PolyseedSeed) else SettingsConstants.SETTING__POLYSEED_WORDLIST_LANGUAGE)
        self.decoder = DecodeQR(wordlist_language_code=wordlist_language_code)
        ScanScreen(decoder=self.decoder, instructions_text="Scan your SeedQR").display()
        if self.decoder.is_complete:
            if self.decoder.is_seed:
                seed_mnemonic = self.decoder.get_seed_phrase()
                # Found a valid mnemonic seed! But does it match?
                if seed_mnemonic != self.seed.mnemonic_list:
                    DireWarningScreen(
                        title="Confirm SeedQR",
                        status_headline="Error!",
                        text="Your transcribed SeedQR does not match your original seed!",
                        show_back_button=False,
                        button_data=["Review SeedQR"],
                    ).display()
                    return Destination(BackStackView, skip_current_view=True)
                LargeIconStatusScreen(
                    title="Confirm SeedQR",
                    status_headline="Success!",
                    text="Your transcribed SeedQR successfully scanned and yielded the same seed.",
                    show_back_button=False,
                    button_data=["OK"],
                ).display()
                return Destination(SeedOptionsView, view_args={"seed_num": self.seed_num})
            # Will this case ever happen? Will trigger if a different kind of QR code is scanned
            DireWarningScreen(
                title="Confirm SeedQR",
                status_headline="Error!",
                text="Your transcribed SeedQR could not be read!",
                show_back_button=False,
                button_data=["Review SeedQR"],
            ).display()
            return Destination(BackStackView, skip_current_view=True)
