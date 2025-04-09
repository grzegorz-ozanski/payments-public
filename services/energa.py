from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from payment import Payment
from .service import AuthElement, Service
from log import setup_logging

log = setup_logging(__name__, 'DEBUG')


class Energa(Service):
    def __init__(self, keystore_user):
        user_input = AuthElement(By.ID, "pt1:s13:it1::content")
        password_input = AuthElement(By.ID, "pt1:s13:it2::content")
        url = "https://24.energa.pl"
        keystore_service = self.__class__.__name__.lower()
        super().__init__(url, keystore_service, keystore_user, user_input, password_input)

    def _get_maintenance_buttons(self, by):
        if by == By.ID:
            return self.browser.wait_for_elements("pt1:r1:0:cb1", By.ID, 0)
        else:  # By.XPATH
            return [b for b in self.browser.wait_for_elements("//button", By.XPATH) if "PRZEJDŹ DO ENERGA24" in b.text]

    def _get_due_date(self):
        details_class = "seeDetails"
        date_span_id = "pt1:s1:r1:0:r3:0:lv2:0:pgl13"
        date_value_class = "textViolet"
        details = self.browser.find_element(By.CLASS_NAME, details_class)
        details.click()
        date_span = self.browser.wait_for_elements(date_span_id, By.ID, 3)
        due_date = date_span[0].find_element(By.CLASS_NAME, date_value_class).text if date_span else ""
        self.browser.back()
        return due_date

    def _get_amounts(self):
        # Handle a situation when there are some "Przejdź do Energa24" maintenance buttons
        # prior to amount value (and yes, they can be multiple)
        retries = 10
        amounts = None
        for i in range(retries):
            amounts = self.browser.wait_for_elements("payAmount", delay=1)
            if amounts is None:
                buttons = self._get_maintenance_buttons(By.ID)
                if buttons:
                    buttons[0].click()
            else:
                log.debug(
                    "Find amounts entry in {0}{1} attempt".format(i + 1, {0: "st", 1: "nd", 2: "rd"}.get(i, "th")))
                break
        return amounts

    def get_payments(self):
        log.info("Getting payments...")
        accounts = self.browser.wait_for_elements("pbToolbar")
        if accounts is None:
            print(self.browser.page_source)
        accounts_ids = [x.get_property("id") for x in accounts]
        log.debug("Identified %d accounts" % len(accounts_ids))
        payments = []
        next_id = 0
        for account_id in accounts_ids:
            print(f'...account {next_id+1} of {len(accounts_ids)}')
            log.debug("Processing account '%s'" % account_id)
            account = self.browser.wait_for_element(account_id, By.ID)
            if account:
                log.debug("Opening account page")
                account.click()
            log.debug("Getting payment")
            amounts = self._get_amounts()
            for amount in amounts:
                account = self._get_account(self.browser.find_element(By.ID, "pt1:pt_ot20").text)
                value = amount.text
                due_date = self._get_due_date()
                log.debug("Got amount '%s' of account '%s'" % (value, account))
                payments.append(Payment(value, due_date, account))
            log.debug("Moving to the next account")
            if account_id != accounts_ids[-1]:
                # self.driver.find_element(By.ID, "pt1:close_popup").click()
                menu = self.browser.find_element(By.ID, "pt1:pt_pgl11")
                item = self.browser.find_element(By.ID, f"pt1:pt_i2:{next_id}:pt_cl1")
                next_id += 1
                ActionChains(self.browser.browser).move_to_element(menu).click(item).perform()
                # self.login()
                # self.driver.wait_for_element(self.user_input.selector, self.user_input.by)

        return payments
