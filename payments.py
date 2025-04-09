class Payments:

    def __init__(self, browser, services, debug_mode=False):
        self.debug_mode = debug_mode
        self.browser = browser
        self.services = services

    def collect(self):
        payments = []
        for service in self.services:
            try:
                print("Processing service %s..." % service.name)
                service.login(self.browser)
                payment = service.get_payments()
                payments += sorted(payment, key=lambda value: value.account.key)
                service.logout()
            except Exception as e:
                print(e)
                print("Cannot get payments for service %s!" % service.name)
        for payment in payments:
            # payment.print(self.debug_mode)
            payment.print(True)
        self.browser.quit()
