from conans import ConanFile


class DateConan(ConanFile):
    name = "Date"
    version = "3.01"
    url = "https://github.com/Esri/date/tree/runtimecore"
    license = "https://github.com/Esri/date/blob/runtimecore/LICENSE.txt"
    description = "Howard Hinnant's TZDB parser."

    # RTC specific triple
    settings = "platform_architecture_target"

    def package(self):
        base = self.source_folder + "/"
        relative = "3rdparty/date/"

        # headers
        self.copy("*.h*", src=base + "include", dst=relative + "include")

        # libraries
        output = "output/" + str(self.settings.platform_architecture_target) + "/staticlib"
        self.copy("*" + self.name + "*", src=base + "../../" + output, dst=output)