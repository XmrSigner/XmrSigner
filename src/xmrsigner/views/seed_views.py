import random
import time

from binascii import hexlify
from typing import List
from math import ceil

from xmrsigner.controller import Controller
from xmrsigner.gui.components import (
    FontAwesomeIconConstants,
    SeedSignerCustomIconConstants
)
from xmrsigner.gui.screens import (
    RET_CODE__BACK_BUTTON,
    ButtonListScreen,
    WarningScreen,
    DireWarningScreen,
    seed_screens
)
from xmrsigner.gui.screens.screen import (
    LargeIconStatusScreen,
    LoadingScreenThread,
    QRDisplayScreen
)
from xmrsigner.models.decode_qr import DecodeQR
from xmrsigner.models.encode_qr import EncodeQR
from xmrsigner.models.psbt_parser import PSBTParser
from xmrsigner.models.qr_type import QRType
from xmrsigner.models.seed import InvalidSeedException, Seed
from xmrsigner.models.polyseed import PolyseedSeed
from xmrsigner.models.settings import SettingsConstants
from xmrsigner.models.settings_definition import SettingsDefinition
from xmrsigner.models.threads import BaseThread, ThreadsafeCounter
from xmrsigner.views.psbt_views import PSXMRhangeDetailsView
from xmrsigner.views.scan_views import ScanView
from xmrsigner.views.wallet_views import WalletViewKeyQRView

from .view import (
    NotYetImplementedView,
    View, Destination,
    BackStackView,
    MainMenuView
)




class SeedsMenuView(View):
    def __init__(self):
        super().__init__()
        self.seeds = []
        for seed in self.controller.storage.seeds:
            print(type(seed))
            print(isinstance(seed, PolyseedSeed))
            self.seeds.append({
                'fingerprint': seed.get_fingerprint(self.settings.get_value(SettingsConstants.SETTING__NETWORK)),
                'has_passphrase': seed.has_passphrase,
                'polyseed': isinstance(seed, PolyseedSeed),
                'mymonero': seed.is_my_monero
            })


    def run(self):
        if not self.seeds:
            # Nothing to do here unless we have a seed loaded
            return Destination(LoadSeedView, clear_history=True)

        button_data = []
        for seed in self.seeds:
            button_data.append(
                (
                    seed["fingerprint"],
                    SeedSignerCustomIconConstants.FINGERPRINT,
                    'purple' if seed['polyseed'] else 'blue' if not seed['mymonero'] else 'red',
                    None,
                    FontAwesomeIconConstants.LOCK if seed['has_passphrase'] else None
                )
            )
        button_data.append("Load a seed")

        selected_menu_num = ButtonListScreen(
            title="In-Memory Seeds",
            is_button_text_centered=False,
            button_data=button_data
        ).display()

        if len(self.seeds) > 0 and selected_menu_num < len(self.seeds):
            return Destination(SeedOptionsView, view_args={"seed_num": selected_menu_num})

        elif selected_menu_num == len(self.seeds):
            return Destination(LoadSeedView)

        elif selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)



"""****************************************************************************
    Loading seeds, passphrases, etc
****************************************************************************"""
class LoadSeedView(View):
    def run(self):
        SEED_QR = (" Scan a SeedQR", FontAwesomeIconConstants.QRCODE)
        TYPE_13WORD = ("Enter 13-word seed", FontAwesomeIconConstants.KEYBOARD)
        TYPE_25WORD = ("Enter 25-word seed", FontAwesomeIconConstants.KEYBOARD)
        TYPE_POLYSEED = ("Enter Polyseed", FontAwesomeIconConstants.KEYBOARD)
        CREATE = (" Create a seed", FontAwesomeIconConstants.PLUS)
        button_data=[
            SEED_QR,
            TYPE_13WORD,
            TYPE_25WORD,
            TYPE_POLYSEED,
            CREATE,
        ]

        selected_menu_num = ButtonListScreen(
            title="Load A Seed",
            is_button_text_centered=False,
            button_data=button_data
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        if button_data[selected_menu_num] == SEED_QR:
            from .scan_views import ScanView
            return Destination(ScanView)
        
        elif button_data[selected_menu_num] == TYPE_13WORD:
            self.controller.storage.init_pending_mnemonic(num_words=13)
            return Destination(SeedMnemonicEntryView)

        elif button_data[selected_menu_num] == TYPE_25WORD:
            self.controller.storage.init_pending_mnemonic(num_words=25)
            return Destination(SeedMnemonicEntryView)

        elif button_data[selected_menu_num] == TYPE_POLYSEED:
            self.controller.storage.init_pending_mnemonic(num_words=16)
            return Destination(PolyseedMnemonicEntryView)

        elif button_data[selected_menu_num] == CREATE:
            from .tools_views import ToolsMenuView
            return Destination(ToolsMenuView)


class SeedMnemonicEntryView(View):

    def __init__(self, cur_word_index: int = 0, is_calc_final_word: bool=False):
        super().__init__()
        self.cur_word_index = cur_word_index
        self.cur_word = self.controller.storage.get_pending_mnemonic_word(cur_word_index)
        self.is_calc_final_word = is_calc_final_word


    def run(self):
        ret = seed_screens.SeedMnemonicEntryScreen(
            title=f"Seed Word #{self.cur_word_index + 1}",  # Human-readable 1-indexing!
            initial_letters=list(self.cur_word) if self.cur_word else ["a"],
            wordlist=Seed.get_wordlist(wordlist_language_code=self.settings.get_value(SettingsConstants.SETTING__WORDLIST_LANGUAGE)),
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            if self.cur_word_index > 0:
                return Destination(BackStackView)
            else:
                self.controller.storage.discard_pending_mnemonic()
                return Destination(MainMenuView)
        
        # ret will be our new mnemonic word
        self.controller.storage.update_pending_mnemonic(ret, self.cur_word_index)

        if self.is_calc_final_word and self.cur_word_index == self.controller.storage.pending_mnemonic_length - 2:  # TODO: 2024-06-30, clean up, this code is now functional but uggly as fuck!
            # Time to calculate the last word. User must decide how they want to specify
            # the last bits of entropy for the final word.
            from xmrsigner.views.tools_views import ToolsCalcFinalWordShowFinalWordView
            # return Destination(ToolsCalcFinalWordFinalizePromptView)  # TODO: expire 2024-06-30, lean it up
            return Destination(ToolsCalcFinalWordShowFinalWordView, view_args=dict(coin_flips="0" * 7))

        if self.is_calc_final_word and self.cur_word_index == self.controller.storage.pending_mnemonic_length - 1:
            # Time to calculate the last word. User must either select a final word to
            # contribute entropy to the checksum word OR we assume 0 ("abandon").
            from xmrsigner.views.tools_views import ToolsCalcFinalWordShowFinalWordView
            return Destination(ToolsCalcFinalWordShowFinalWordView)

        if self.cur_word_index < self.controller.storage.pending_mnemonic_length - 1:
            return Destination(
                SeedMnemonicEntryView,
                view_args={
                    "cur_word_index": self.cur_word_index + 1,
                    "is_calc_final_word": self.is_calc_final_word
                }
            )
        else:
            # Attempt to finalize the mnemonic
            try:
                self.controller.storage.convert_pending_mnemonic_to_pending_seed()
            except InvalidSeedException:
                return Destination(SeedMnemonicInvalidView)

            return Destination(SeedFinalizeView)


class PolyseedMnemonicEntryView(SeedMnemonicEntryView):

    def __init__(self, cur_word_index: int = 0):
        super().__init__(cur_word_index, False)

    def run(self):
        ret = seed_screens.SeedMnemonicEntryScreen(
            title=f"Polyseed Word #{self.cur_word_index + 1}",  # Human-readable 1-indexing!
            initial_letters=list(self.cur_word) if self.cur_word else ["a"],
            wordlist=PolyseedSeed.get_wordlist(wordlist_language_code=self.settings.get_value(SettingsConstants.SETTING__WORDLIST_LANGUAGE)),
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            if self.cur_word_index > 0:
                return Destination(BackStackView)
            else:
                self.controller.storage.discard_pending_mnemonic()
                return Destination(MainMenuView)
        
        # ret will be our new mnemonic word
        self.controller.storage.update_pending_mnemonic(ret, self.cur_word_index)

        if self.cur_word_index < self.controller.storage.pending_mnemonic_length - 1:
            return Destination(
                PolyseedMnemonicEntryView,
                view_args={
                    "cur_word_index": self.cur_word_index + 1
                }
            )
        else:
            # Attempt to finalize the mnemonic
            try:
                self.controller.storage.convert_pending_mnemonic_to_pending_polyseed()
            except InvalidSeedException:
                return Destination(SeedMnemonicInvalidView, view_args={'polyseed': True})
            return Destination(SeedFinalizeView)


class SeedMnemonicInvalidView(View):

    def __init__(self, polyseed: bool = False):
        super().__init__()
        self.mnemonic: List[str] = self.controller.storage.pending_mnemonic
        self.polyseed = polyseed


    def run(self):
        EDIT = "Review & Edit"
        DISCARD = ("Discard", None, None, "red")
        button_data = [EDIT, DISCARD]

        selected_menu_num = WarningScreen(
            title="Invalid Mnemonic!",
            status_headline=None,
            text=f"Checksum failure; not a valid seed phrase.",
            show_back_button=False,
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == EDIT:
            return Destination(
                PolyseedMnemonicEntryView if self.polyseed else SeedMnemonicEntryView,
                view_args={"cur_word_index": 0}
            )
        elif button_data[selected_menu_num] == DISCARD:
            self.controller.storage.discard_pending_mnemonic()
            return Destination(MainMenuView)


class SeedFinalizeView(View):

    def __init__(self):
        super().__init__()
        self.seed = self.controller.storage.get_pending_seed()
        self.fingerprint = self.seed.get_fingerprint(network=self.settings.get_value(SettingsConstants.SETTING__NETWORK))
        self.polyseed = isinstance(self.seed, PolyseedSeed)

    def run(self):
        FINALIZE = "Done"
        PASSPHRASE = ("Add Passphrase", FontAwesomeIconConstants.LOCK)
        button_data = []

        button_data.append(FINALIZE)

        if (not self.polyseed and self.settings.get_value(SettingsConstants.SETTING__MONERO_SEED_PASSPHRASE) == SettingsConstants.OPTION__ENABLED) or (self.polyseed and self.settings.get_value(SettingsConstants.SETTING__POLYSEED_PASSPHRASE) == SettingsConstants.OPTION__ENABLED):
            button_data.append(PASSPHRASE)

        selected_menu_num = seed_screens.SeedFinalizeScreen(
            fingerprint=self.fingerprint,
            polyseed=self.polyseed,
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == FINALIZE:
            seed_num = self.controller.storage.finalize_pending_seed()
            return Destination(SeedOptionsView, view_args={"seed_num": seed_num}, clear_history=True)

        elif button_data[selected_menu_num] == PASSPHRASE:
            return Destination(SeedAddPassphraseView)


class SeedAddPassphraseView(View):
    def __init__(self):
        super().__init__()
        self.seed = self.controller.storage.get_pending_seed()


    def run(self):
        ret = seed_screens.SeedAddPassphraseScreen(passphrase=self.seed.passphrase_str).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        # The new passphrase will be the return value
        self.seed.set_passphrase(ret)
        return Destination(SeedReviewPassphraseView)



class SeedReviewPassphraseView(View):
    """
        Display the completed passphrase back to the user.
    """
    def __init__(self):
        super().__init__()
        self.seed = self.controller.storage.get_pending_seed()


    def run(self):
        EDIT = "Edit passphrase"
        DONE = "Done"
        button_data = [EDIT, DONE]

        # Get the before/after fingerprints
        network = self.settings.get_value(SettingsConstants.SETTING__NETWORK)
        passphrase = self.seed.passphrase
        fingerprint_with = self.seed.get_fingerprint(network=network)
        self.seed.set_passphrase(None)
        fingerprint_without = self.seed.get_fingerprint(network=network)
        self.seed.set_passphrase(passphrase)
        
        # Because we have ane explicit "Edit" button, we disable "BACK" to keep the
        # routing options sane.
        selected_menu_num = seed_screens.SeedReviewPassphraseScreen(
            fingerprint_without=fingerprint_without,
            fingerprint_with=fingerprint_with,
            passphrase=self.seed.passphrase,
            polyseed=isinstance(self.seed, PolyseedSeed),
            button_data=button_data,
            show_back_button=False,
        ).display()

        if button_data[selected_menu_num] == EDIT:
            return Destination(SeedAddPassphraseView)
        
        elif button_data[selected_menu_num] == DONE:
            seed_num = self.controller.storage.finalize_pending_seed()
            return Destination(SeedOptionsView, view_args={"seed_num": seed_num}, clear_history=True)
            
            
            
class SeedDiscardView(View):
    def __init__(self, seed_num: int = None):
        super().__init__()
        self.seed_num = seed_num
        if self.seed_num is not None:
            self.seed = self.controller.get_seed(self.seed_num)
        else:
            self.seed = self.controller.storage.pending_seed


    def run(self):
        KEEP = "Keep Seed"
        DISCARD = ("Discard", None, None, "red")
        button_data = [KEEP, DISCARD]

        fingerprint = self.seed.get_fingerprint(self.settings.get_value(SettingsConstants.SETTING__NETWORK))
        selected_menu_num = WarningScreen(
            title="Discard Seed?",
            status_headline=None,
            text=f"Wipe seed {fingerprint} from the device?",
            show_back_button=False,
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == KEEP:
            # Use skip_current_view=True to prevent BACK from landing on this warning screen
            if self.seed_num is not None:
                return Destination(SeedOptionsView, view_args={"seed_num": self.seed_num}, skip_current_view=True)
            else:
                return Destination(SeedFinalizeView, skip_current_view=True)

        elif button_data[selected_menu_num] == DISCARD:
            if self.seed_num is not None:
                self.controller.discard_seed(self.seed_num)
            else:
                self.controller.storage.clear_pending_seed()
            return Destination(MainMenuView, clear_history=True)



"""****************************************************************************
    Views for actions on individual seeds:
****************************************************************************"""
class SeedOptionsView(View):
    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num
        self.seed = self.controller.get_seed(self.seed_num)

    def run(self):
        from xmrsigner.views.psbt_views import PSBTOverviewView

        SCAN_PSBT = ("Scan PSBT", FontAwesomeIconConstants.QRCODE)
        REVIEW_PSBT = "Review PSBT"
        VERIFY_ADDRESS = "Verify Addr"
        VIEW_ONLY_WALLET = ("View only Wallet")
        BACKUP = ("Backup Seed", None, None, None, SeedSignerCustomIconConstants.SMALL_CHEVRON_RIGHT)
        CONVERT_POOLYSEED = ('Convert to Monero seed')
        DISCARD = ("Discard Seed", None, None, "red")

        button_data = []

        if self.controller.unverified_address:
            if self.controller.resume_main_flow == Controller.FLOW__VERIFY_SINGLESIG_ADDR:
                # Jump straight back into the single sig addr verification flow
                self.controller.resume_main_flow = None
                return Destination(SeedAddressVerificationView, view_args=dict(seed_num=self.seed_num), skip_current_view=True)

            addr = self.controller.unverified_address["address"][:7]
            VERIFY_ADDRESS += f" {addr}"
            button_data.append(VERIFY_ADDRESS)
        
        if self.controller.psbt:
            if PSBTParser.has_matching_input_fingerprint(self.controller.psbt, self.seed, network=self.settings.get_value(SettingsConstants.SETTING__NETWORK)):
                if self.controller.resume_main_flow and self.controller.resume_main_flow == Controller.FLOW__PSBT:
                    # Re-route us directly back to the start of the PSBT flow 
                    self.controller.resume_main_flow = None
                    self.controller.psbt_seed = self.seed
                    return Destination(PSBTOverviewView, skip_current_view=True)
            else:
                # This seed does not seem to be a signer for this PSBT
                # TODO:SEEDSIGNER: How sure are we? Should disable this entirely if we're 100% sure?
                REVIEW_PSBT += " (?)"
            button_data.append(REVIEW_PSBT)
        else:
            button_data.append(SCAN_PSBT)
        
        button_data.append(VIEW_ONLY_WALLET)
        button_data.append(BACKUP)

        if isinstance(self.seed, PolyseedSeed):
            button_data.append(CONVERT_POOLYSEED)

        button_data.append(DISCARD)

        selected_menu_num = seed_screens.SeedOptionsScreen(
            button_data=button_data,
            fingerprint=self.seed.get_fingerprint(self.settings.get_value(SettingsConstants.SETTING__NETWORK)),
            polyseed=isinstance(self.seed, PolyseedSeed),
            has_passphrase=self.seed.passphrase is not None
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            # Force BACK to always return to the Main Menu
            return Destination(MainMenuView)

        if button_data[selected_menu_num] == REVIEW_PSBT:
            self.controller.psbt_seed = self.controller.get_seed(self.seed_num)
            return Destination(PSBTOverviewView)

        if button_data[selected_menu_num] == SCAN_PSBT:
            from xmrsigner.views.scan_views import ScanView
            return Destination(ScanView)

        if button_data[selected_menu_num] == VERIFY_ADDRESS:
            return Destination(SeedAddressVerificationView, view_args={"seed_num": self.seed_num})

        if button_data[selected_menu_num] == BACKUP:
            return Destination(SeedBackupView, view_args={"seed_num": self.seed_num})

        if button_data[selected_menu_num] == CONVERT_POOLYSEED:
            if isinstance(self.seed, PolyseedSeed):
                self.controller.replace_seed(self.seed_num, self.seed.to_monero_seed(None))
                return Destination(SeedOptionsView, view_args={"seed_num": self.seed_num}, skip_current_view=True)
            else:
                DireWarningScreen(
                    title='Not a Polyseed',
                    status_headline='Error!',
                    text="Can't convert to monero seed!",
                    show_back_button=False,
                    button_data=['OK'],
                ).display()
                return Destination(BackStackView, skip_current_view=True)

        if button_data[selected_menu_num] == VIEW_ONLY_WALLET:  # TODO: 2024-06-10: finish implementation
            return Destination(WalletViewKeyQRView, view_args={'seed_num': self.seed_num})

        if button_data[selected_menu_num] == DISCARD:
            return Destination(SeedDiscardView, view_args={"seed_num": self.seed_num})


class SeedBackupView(View):
    def __init__(self, seed_num):
        super().__init__()
        self.seed_num = seed_num
        self.seed = self.controller.get_seed(self.seed_num)
    

    def run(self):
        VIEW_WORDS = "View Seed Words"
        EXPORT_SEEDQR = "Export as SeedQR"
        button_data = [VIEW_WORDS, EXPORT_SEEDQR]

        selected_menu_num = ButtonListScreen(
            title="Backup Seed",
            button_data=button_data,
            is_bottom_list=True,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_num] == VIEW_WORDS:
            return Destination(SeedWordsWarningView, view_args={"seed_num": self.seed_num})

        elif button_data[selected_menu_num] == EXPORT_SEEDQR:
            return Destination(SeedTranscribeSeedQRFormatView, view_args={"seed_num": self.seed_num})


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
            view_args={"seed_num": self.seed_num, "page_index": 0},
            skip_current_view=True,  # Prevent going BACK to WarningViews
        )
        if self.settings.get_value(SettingsConstants.SETTING__DIRE_WARNINGS) == SettingsConstants.OPTION__DISABLED:  # TODO: no warning or different warning for view keys, adapt before 2024-06-10
            # Forward straight to showing the words
            return destination

        selected_menu_num = DireWarningScreen(  # TODO: see todo above, adapt text to master key and view keys before 2024-06-10
            text="""You must keep your seed words private & away from all online devices.""",
        ).display()

        if selected_menu_num == 0:
            # User clicked "I Understand"
            return destination

        elif selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)



class SeedWordsView(View):
    def __init__(self, seed_num: int, page_index: int = 0):
        super().__init__()
        self.seed_num = seed_num
        if self.seed_num is None:
            self.seed = self.controller.storage.get_pending_seed()
        else:
            self.seed = self.controller.get_seed(self.seed_num)
        self.page_index = page_index
        self.num_pages=int(ceil(len(self.seed.mnemonic_list)/4))


    def run(self):
        NEXT = "Next"
        DONE = "Done"

        # Slice the mnemonic to our current 4-word section
        words_per_page = 4

        mnemonic = self.seed.mnemonic_display_list
        words = mnemonic[self.page_index*words_per_page:(self.page_index + 1)*words_per_page]

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
            else:
                return Destination(SeedWordsView, view_args=dict(seed_num=self.seed_num, page_index=self.page_index + 1))

        elif button_data[selected_menu_num] == DONE:
            # Must clear history to avoid BACK button returning to private info
            return Destination(SeedWordsBackupTestPromptView, view_args=dict(seed_num=self.seed_num))



"""****************************************************************************
    Seed Words Backup Test
****************************************************************************"""
class SeedWordsBackupTestPromptView(View):
    def __init__(self, seed_num: int):
        self.seed_num = seed_num
    

    def run(self):
        VERIFY = "Verify"
        SKIP = "Skip"
        button_data = [VERIFY, SKIP]
        selected_menu_num = seed_screens.SeedWordsBackupTestPromptScreen(
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == VERIFY:
            return Destination(SeedWordsBackupTestView, view_args=dict(seed_num=self.seed_num))

        elif button_data[selected_menu_num] == SKIP:
            if self.seed_num is not None:
                return Destination(SeedOptionsView, view_args=dict(seed_num=self.seed_num))
            else:
                return Destination(SeedFinalizeView)



class SeedWordsBackupTestView(View):
    def __init__(self, seed_num: int, confirmed_list: List[bool] = None, cur_index: int = None):
        super().__init__()
        self.seed_num = seed_num
        if self.seed_num is None:
            self.seed = self.controller.storage.get_pending_seed()
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
            else:
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
        REVIEW = "Review Seed Words"
        RETRY = "Try Again"
        button_data = [REVIEW, RETRY]

        selected_menu_num = DireWarningScreen(
            title="Verification Error",
            show_back_button=False,
            status_headline=f"Wrong Word!",
            text=f"Word #{self.cur_index + 1} is not \"{self.wrong_word}\"!",
            button_data=button_data,
        ).display()

        if button_data[selected_menu_num] == REVIEW:
            return Destination(SeedWordsView, view_args=dict(seed_num=self.seed_num))
        
        elif button_data[selected_menu_num] == RETRY:
            return Destination(SeedWordsBackupTestView, view_args=dict(seed_num=self.seed_num, confirmed_list=self.confirmed_list, cur_index=self.cur_index))
    


class SeedWordsBackupTestSuccessView(View):
    def __init__(self, seed_num: int):
        self.seed_num = seed_num
    
    def run(self):
        LargeIconStatusScreen(
            title="Backup Verified",
            show_back_button=False,
            status_headline="Success!",
            text="All mnemonic backup words were successfully verified!",
            button_data=["OK"]
        ).display()

        if self.seed_num is not None:
            return Destination(SeedOptionsView, view_args=dict(seed_num=self.seed_num), clear_history=True)
        else:
            return Destination(SeedFinalizeView)



"""****************************************************************************
    Export as SeedQR
****************************************************************************"""
class SeedTranscribeSeedQRFormatView(View): # TODO: expire 2024-06-04: adapt to polyseed, monero seed and view keys - we don't supportMyMonero keys for export. Wait, need to check again, seems that is meant to draw your QR codes on paper, so it would not really make sense for view keys, not? Would it? Think again about before taking decision!
    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num

    def run(self):
        seed = self.controller.get_seed(self.seed_num)
        if len(seed.mnemonic_list) == 12:
            STANDARD = "Standard: 25x25"
            COMPACT = "Compact: 21x21"
            num_modules_standard = 25
            num_modules_compact = 21
        else:
            STANDARD = "Standard: 29x29"
            COMPACT = "Compact: 25x25"
            num_modules_standard = 29
            num_modules_compact = 25

        if self.settings.get_value(SettingsConstants.SETTING__COMPACT_SEEDQR) != SettingsConstants.OPTION__ENABLED:
            # Only configured for standard SeedQR
            return Destination(
                SeedTranscribeSeedQRWarningView,
                view_args={
                    "seed_num": self.seed_num,
                    "seedqr_format": QRType.SEED__SEEDQR,
                    "num_modules": num_modules_standard,
                },
                skip_current_view=True,
            )

        button_data = [STANDARD, COMPACT]

        selected_menu_num = seed_screens.SeedTranscribeSeedQRFormatScreen(
            title="SeedQR Format",
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
                    "seed_num": self.seed_num,
                    "seedqr_format": seedqr_format,
                    "num_modules": num_modules,
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
                "seed_num": self.seed_num,
                "seedqr_format": self.seedqr_format,
                "num_modules": self.num_modules,
            },
            skip_current_view=True,  # Prevent going BACK to WarningViews
        )

        if self.settings.get_value(SettingsConstants.SETTING__DIRE_WARNINGS) == SettingsConstants.OPTION__DISABLED:
            # Forward straight to transcribing the SeedQR
            return destination

        selected_menu_num = DireWarningScreen(
                status_headline="SeedQR is your private key!",
            text="""Never photograph it or scan it into an online device.""",
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        else:
            # User clicked "I Understand"
            return destination


class SeedTranscribeSeedQRWholeQRView(View):
    def __init__(self, seed_num: int, seedqr_format: str, num_modules: int):
        super().__init__()
        self.seed_num = seed_num
        self.seedqr_format = seedqr_format
        self.num_modules = num_modules
        self.seed = self.controller.get_seed(seed_num)
    

    def run(self):
        e = EncodeQR(
            seed_phrase=self.seed.mnemonic_list,
            qr_type=self.seedqr_format,
            wordlist_language_code=self.settings.get_value(SettingsConstants.SETTING__WORDLIST_LANGUAGE)
        )
        data = e.next_part()

        ret = seed_screens.SeedTranscribeSeedQRWholeQRScreen(
            qr_data=data,
            num_modules=self.num_modules,
        ).display()

        if ret == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        else:
            return Destination(
                SeedTranscribeSeedQRZoomedInView,
                view_args={
                    "seed_num": self.seed_num,
                    "seedqr_format": self.seedqr_format
                }
            )


class SeedTranscribeSeedQRZoomedInView(View):
    def __init__(self, seed_num: int, seedqr_format: str):
        super().__init__()
        self.seed_num = seed_num
        self.seedqr_format = seedqr_format
        self.seed = self.controller.get_seed(seed_num)
    

    def run(self):
        e = EncodeQR(
            seed_phrase=self.seed.mnemonic_list,
            qr_type=self.seedqr_format,
            wordlist_language_code=self.settings.get_value(SettingsConstants.SETTING__WORDLIST_LANGUAGE)
        )
        data = e.next_part()

        if len(self.seed.mnemonic_list) == 24: # TODO: expire 2024-06-04, can only be 25 (monero seed) or 16 (polyseed)
            if self.seedqr_format == QRType.SEED__COMPACTSEEDQR:
                num_modules = 25  # TODO: expire 2024-06-30, from there come this numbers, is this not some data comming from QR code constraints? Would it no be wise to get the number from there instead of this???
            else:
                num_modules = 29
        else:
            if self.seedqr_format == QRType.SEED__COMPACTSEEDQR:
                num_modules = 21
            else:
                num_modules = 25

        seed_screens.SeedTranscribeSeedQRZoomedInScreen(
            qr_data=data,
            num_modules=num_modules,
        ).display()

        return Destination(SeedTranscribeSeedQRConfirmQRPromptView, view_args={"seed_num": self.seed_num})



class SeedTranscribeSeedQRConfirmQRPromptView(View):
    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num
        self.seed = self.controller.get_seed(seed_num)
    

    def run(self):
        SCAN = ("Confirm SeedQR", FontAwesomeIconConstants.QRCODE)
        DONE = "Done"
        button_data = [SCAN, DONE]

        selected_menu_option = seed_screens.SeedTranscribeSeedQRConfirmQRPromptScreen(
            title="Confirm SeedQR?",
            button_data=button_data,
        ).display()

        if selected_menu_option == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)

        elif button_data[selected_menu_option] == SCAN:
            return Destination(SeedTranscribeSeedQRConfirmScanView, view_args={"seed_num": self.seed_num})

        elif button_data[selected_menu_option] == DONE:
            return Destination(SeedOptionsView, view_args={"seed_num": self.seed_num}, clear_history=True)



class SeedTranscribeSeedQRConfirmScanView(View):
    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num
        self.seed = self.controller.get_seed(seed_num)

    def run(self):
        from xmrsigner.gui.screens.scan_screens import ScanScreen

        # Run the live preview and QR code capture process
        # TODO:SEEDSIGNER: Does this belong in its own BaseThread?
        wordlist_language_code = self.settings.get_value(SettingsConstants.SETTING__WORDLIST_LANGUAGE)
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
                
                else:
                    LargeIconStatusScreen(
                        title="Confirm SeedQR",
                        status_headline="Success!",
                        text="Your transcribed SeedQR successfully scanned and yielded the same seed.",
                        show_back_button=False,
                        button_data=["OK"],
                    ).display()

                    return Destination(SeedOptionsView, view_args={"seed_num": self.seed_num})

            else:
                # Will this case ever happen? Will trigger if a different kind of QR code is scanned
                DireWarningScreen(
                    title="Confirm SeedQR",
                    status_headline="Error!",
                    text="Your transcribed SeedQR could not be read!",
                    show_back_button=False,
                    button_data=["Review SeedQR"],
                ).display()

                return Destination(BackStackView, skip_current_view=True)



"""****************************************************************************
    Address verification
****************************************************************************"""
class AddressVerificationStartView(View):  # TODO: expire 2024-06-04, remove BTC related stuff, make it work for monero
    def __init__(self, address: str, script_type: str, network: str):
        super().__init__()
        self.controller.unverified_address = dict(
            address=address,
            script_type=script_type,
            network=network
        )


    def run(self):
        if self.controller.unverified_address["script_type"] == SettingsConstants.NESTED_SEGWIT:
            # No way to differentiate single sig from multisig
            return Destination(AddressVerificationSigTypeView, skip_current_view=True)

        if self.controller.unverified_address["script_type"] == SettingsConstants.NATIVE_SEGWIT:
            if len(self.controller.unverified_address["address"]) >= 62:
                # Mainnet/testnet are 62, regtest is 64
                sig_type = SettingsConstants.MULTISIG
                if self.controller.multisig_wallet_descriptor:
                    # Can jump straight to the brute-force verification View
                    destination = Destination(SeedAddressVerificationView)
                else:
                    self.controller.resume_main_flow = Controller.FLOW__VERIFY_MULTISIG_ADDR
                    destination = Destination(LoadMultisigWalletDescriptorView)

            else:
                sig_type = SettingsConstants.SINGLE_SIG
                destination = Destination(SeedSingleSigAddressVerificationSelectSeedView)

        elif self.controller.unverified_address["script_type"] == SettingsConstants.TAPROOT:
            destination = Destination(NotYetImplementedView)

        elif self.controller.unverified_address["script_type"] == SettingsConstants.LEGACY_P2PKH:
            # TODO:SEEDSIGNER: detect single sig vs multisig or have to prompt?
            destination = Destination(NotYetImplementedView)

        derivation_path = PSBTParser.calc_derivation(
            network=self.controller.unverified_address["network"],
            wallet_type=sig_type,
            script_type=self.controller.unverified_address["script_type"]
        )

        self.controller.unverified_address["sig_type"] = sig_type
        self.controller.unverified_address["derivation_path"] = derivation_path

        return destination



class AddressVerificationSigTypeView(View):  # TODO: expire 2024-06-04, remove BTC stuff, make monero work
    def run(self):
        sig_type_settings_entry = SettingsDefinition.get_settings_entry(SettingsConstants.SETTING__SIG_TYPES)
        SINGLE_SIG = sig_type_settings_entry.get_selection_option_display_name_by_value(SettingsConstants.SINGLE_SIG)
        MULTISIG = sig_type_settings_entry.get_selection_option_display_name_by_value(SettingsConstants.MULTISIG)

        button_data = [SINGLE_SIG, MULTISIG]
        selected_menu_num = seed_screens.AddressVerificationSigTypeScreen(
            title="Verify Address",
            text="Sig type can't be auto-detected from this address. Please specify:",
            button_data=button_data,
            is_bottom_list=True,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            self.controller.unverified_address = None
            return Destination(BackStackView)
        
        elif button_data[selected_menu_num] == SINGLE_SIG:
            sig_type = SettingsConstants.SINGLE_SIG
            destination = Destination(SeedSingleSigAddressVerificationSelectSeedView)

        elif button_data[selected_menu_num] == MULTISIG:
            sig_type = SettingsConstants.MULTISIG
            if self.controller.multisig_wallet_descriptor:
                destination = Destination(SeedAddressVerificationView)
            else:
                self.controller.resume_main_flow = Controller.FLOW__VERIFY_MULTISIG_ADDR
                destination = Destination(LoadMultisigWalletDescriptorView)

        self.controller.unverified_address["sig_type"] = sig_type
        derivation_path = PSBTParser.calc_derivation(
            network=self.controller.unverified_address["network"],
            wallet_type=sig_type,
            script_type=self.controller.unverified_address["script_type"]
        )
        self.controller.unverified_address["derivation_path"] = derivation_path

        return destination



class SeedSingleSigAddressVerificationSelectSeedView(View):
    def run(self):
        seeds = self.controller.storage.seeds

        SCAN_SEED = ("Scan a seed", FontAwesomeIconConstants.QRCODE)
        TYPE_13WORD = ("Enter 13-word seed", FontAwesomeIconConstants.KEYBOARD)
        TYPE_25WORD = ("Enter 25-word seed", FontAwesomeIconConstants.KEYBOARD)
        button_data = []

        text = "Load the seed to verify"

        for seed in seeds:
            button_str = seed.get_fingerprint(self.settings.get_value(SettingsConstants.SETTING__NETWORK))
            
            if seed.passphrase is not None:
                # TODO:SEEDSIGNER: Include lock icon on right side of button
                pass
            button_data.append((button_str, SeedSignerCustomIconConstants.FINGERPRINT, "blue"))

            text = "Select seed to verify"

        button_data.append(SCAN_SEED)
        button_data.append(TYPE_13WORD)
        button_data.append(TYPE_25WORD)

        selected_menu_num = seed_screens.SeedSingleSigAddressVerificationSelectSeedScreen(
            title="Verify Address",
            text=text,
            is_button_text_centered=False,
            button_data=button_data
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            return Destination(BackStackView)
        
        if len(seeds) > 0 and selected_menu_num < len(seeds):
            # User selected one of the n seeds
            return Destination(
                SeedAddressVerificationView,
                view_args=dict(
                    seed_num=selected_menu_num,
                )
            )

        self.controller.resume_main_flow = Controller.FLOW__VERIFY_SINGLESIG_ADDR

        if button_data[selected_menu_num] == SCAN_SEED:
            from xmrsigner.views.scan_views import ScanView
            return Destination(ScanView)

        elif button_data[selected_menu_num] in [TYPE_13WORD, TYPE_25WORD]:
            from xmrsigner.views.seed_views import SeedMnemonicEntryView
            if button_data[selected_menu_num] == TYPE_13WORD:
                self.controller.storage.init_pending_mnemonic(num_words=13)
            else:
                self.controller.storage.init_pending_mnemonic(num_words=25)
            return Destination(SeedMnemonicEntryView)



class SeedAddressVerificationView(View):  # TODO: expire 2024-06-15, what is that about??? Remove BTC stuff and make it for monero working. If not needed for monero, remove it
    """
        Creates a worker thread to brute-force calculate addresses. Writes its
        iteration status to a shared `ThreadsafeCounter`.

        The `ThreadsafeCounter` is sent to the display Screen which is monitored in
        its own `ProgressThread` to show the current iteration onscreen.

        Performs single sig verification on `seed_num` if specified, otherwise assumes
        multisig.
    """
    def __init__(self, seed_num: int = None):
        super().__init__()
        self.seed_num = seed_num
        self.is_multisig = self.controller.unverified_address["sig_type"] == SettingsConstants.MULTISIG
        if not self.is_multisig:
            if seed_num is None:
                raise Exception("Can't validate a single sig addr without specifying a seed")
            self.seed_num = seed_num
            self.seed = self.controller.get_seed(seed_num)
        else:
            self.seed = None
        self.address = self.controller.unverified_address["address"]
        self.derivation_path = self.controller.unverified_address["derivation_path"]  # account?
        self.sig_type = self.controller.unverified_address["sig_type"]
        self.network = self.controller.unverified_address["network"]

        # Create the brute-force calculation thread that will run in the background
        # self.addr_verification_thread = None  # TODO: 2024-06-15, nonsense for us


    def run(self):
        # TODO: 2024-06-15, remove all the cluster fuck here, we can verify easy if a address belongs to a wallet in monero
        # script_type_settings_entry = 'REMOVE ME'
        # script_type_display = script_type_settings_entry.get_selection_option_display_name_by_value(self.script_type)
        # sig_type_settings_entry = SettingsDefinition.get_settings_entry(SettingsConstants.SETTING__SIG_TYPES)
        # sig_type_display = sig_type_settings_entry.get_selection_option_display_name_by_value(self.sig_type)
        # network_settings_entry = SettingsDefinition.get_settings_entry(SettingsConstants.SETTING__NETWORK)
        # network_display = network_settings_entry.get_selection_option_display_name_by_value(self.network)
        # mainnet = network_settings_entry.get_selection_option_display_name_by_value(SettingsConstants.MAINNET)
        # Here was before "Brute force address-wallet verification"

        if self.address_belongs_to_wallet:
            # if self.verified_index.cur_count is not None:
                # Successfully verified the addr; update the data
                # self.controller.unverified_address["verified_index"] = self.verified_index.cur_count
                # self.controller.unverified_address["verified_index_is_change"] = self.verified_index_is_change.cur_count == 1
            return Destination(AddressVerificationSuccessView, view_args=dict(seed_num=self.seed_num))
        return Destination(MainMenuView)


class AddressVerificationSuccessView(View):  # TODO: expire 2024-06-12, check if needed for monero, delete or modify
    def __init__(self, seed_num: int):
        super().__init__()
        self.seed_num = seed_num
        if self.seed_num is not None:
            self.seed = self.controller.get_seed(seed_num)
    

    def run(self):
        address = self.controller.unverified_address["address"]
        sig_type = self.controller.unverified_address["sig_type"]
        verified_index = self.controller.unverified_address["verified_index"]
        verified_index_is_change = self.controller.unverified_address["verified_index_is_change"]

        if sig_type == SettingsConstants.MULTISIG:
            source = "multisig"
        else:
            source = f"seed {self.seed.get_fingerprint()}"

        LargeIconStatusScreen(
            status_headline="Address Verified",
            text=f"""{address[:7]} = {source}'s {"change" if verified_index_is_change else "receive"} address #{verified_index}."""
        ).display()

        return Destination(MainMenuView)



class LoadMultisigWalletDescriptorView(View):  # TODO: expire 2024-06-10, adapt to monero
    def run(self):
        SCAN = ("Scan Descriptor", FontAwesomeIconConstants.QRCODE)
        CANCEL = "Cancel"
        button_data = [SCAN, CANCEL]
        selected_menu_num = seed_screens.LoadMultisigWalletDescriptorScreen(
            button_data=button_data,
            show_back_button=False,
        ).display()

        if button_data[selected_menu_num] == SCAN:
            return Destination(ScanView)
        
        elif button_data[selected_menu_num] == CANCEL:
            if self.controller.resume_main_flow == Controller.FLOW__PSBT:
                return Destination(BackStackView)
            else:
                return Destination(MainMenuView)



class MultisigWalletDescriptorView(View):  # TODO: expire 2024-06-10, adapt to monero
    def run(self):
        descriptor = self.controller.multisig_wallet_descriptor

        fingerprints = []
        for key in descriptor.keys:
            fingerprint = hexlify(key.fingerprint).decode()
            fingerprints.append(fingerprint)
        
        policy = descriptor.brief_policy.split("multisig")[0].strip()
        
        RETURN = "Return to PSBT"
        VERIFY = "Verify Addr"
        OK = "OK"

        button_data = [OK]
        if self.controller.resume_main_flow:
            if self.controller.resume_main_flow == Controller.FLOW__PSBT:
                button_data = [RETURN]
            elif self.controller.resume_main_flow == Controller.FLOW__VERIFY_MULTISIG_ADDR and self.controller.unverified_address:
                VERIFY += f""" {self.controller.unverified_address["address"][:7]}"""
                button_data = [VERIFY]

        selected_menu_num = seed_screens.MultisigWalletDescriptorScreen(
            policy=policy,
            fingerprints=fingerprints,
            button_data=button_data,
        ).display()

        if selected_menu_num == RET_CODE__BACK_BUTTON:
            self.controller.multisig_wallet_descriptor = None
            return Destination(BackStackView)
        
        elif button_data[selected_menu_num] == RETURN:
            # Jump straight back to PSBT change verification
            self.controller.resume_main_flow = None
            return Destination(PSXMRhangeDetailsView, view_args=dict(change_address_num=0))

        elif button_data[selected_menu_num] == VERIFY:
            self.controller.resume_main_flow = None
            # TODO:SEEDSIGNER: Route properly when multisig brute-force addr verification is done
            return Destination(SeedAddressVerificationView)

        return Destination(MainMenuView)