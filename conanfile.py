import os
from conans import tools, ConanFile
from conans.errors import ConanInvalidConfiguration


class ConanLexFloatClient(ConanFile):
    name = "lexfloatclient"
    version = '4.5.2'
    description = "LexFloatClient licensing library"
    url = "https://app.cryptlex.com/downloads"
    homepage = "https://cryptlex.com/"
    topics = ("licensing", "cryptlex")
    license = "Proprietary"
    settings = "os", "compiler", "arch", "build_type"
    options = {
        "shared": [True, False],
    }
    default_options = {
        "shared": True,
    }

    @property
    def _la_libname(self):
        return 'LexFloatClient'
    
    def source(self):
        tools.get(**self.conan_data["sources"][self.version][str(self.settings.os)]['shared'])
        if self.settings.os == "Windows":
            tools.get(**self.conan_data["sources"][self.version][str(self.settings.os)]['static'])
        else:
            tools.get(**self.conan_data["sources"][self.version][str(self.settings.os)]['static'])

    @property
    def _package_lib_dir(self):
        if self.settings.os == 'Linux':
            compiler = 'gcc'
            la_arch = {
                'x86': 'i386',
                'x86_64': 'amd64',
                'armv8': 'arm64',
                'armv8.3': 'arm64',
            }[str(self.settings.arch)]
            return os.path.join('libs', compiler, la_arch)

        if self.settings.os == 'Windows':
            la_arch = {
                'x86': 'x86',
                'x86_64': 'x64',
            }[str(self.settings.arch)]
            if self.options.shared:
                if int(str(self.settings.compiler.version)) >= 16:
                    return os.path.join('libs', f'vc16', la_arch)
                else:
                    return os.path.join('libs', f'vc14', la_arch)
            else:
                if self.settings.compiler.runtime in ['MT', 'MTd']:
                    return os.path.join('libs', la_arch + '_MT')
                else:
                    return os.path.join('libs', la_arch)

        if self.settings.os == 'Macos':
            if self.options.shared:
                la_arch = {
                    'x86_64': 'x86_64',
                    'armv8': 'arm64',
                    'armv8.3': 'arm64',
                }[str(self.settings.arch)]
                return os.path.join('libs', 'clang', la_arch)
            else:
                return os.path.join('libs', 'clang', 'universal')
        raise ConanInvalidConfiguration('Libraries for this configuration are not available')

    def system_requirements(self):
        if tools.os_info.is_linux:
            installer = tools.SystemPackageTool()
            if tools.os_info.linux_distro == "fedora" or tools.os_info.linux_distro == "centos" or tools.os_info.linux_distro == "redhat":
                installer.install(f"epel-release")
            installer.install(f"patchelf")

    def package(self):
        self.copy("*.h", dst="include", src='headers')

        if self.options.shared:
            if self.settings.os == 'Linux':
                # cryptlex refuse to add a soname to their so files.
                # this mucks up rpaths on cmake builds
                # so we work around their wy of doing things
                # https://forums.cryptlex.com/t/shared-libraries-without-soname-and-version-number/744
                soname = f'lib{self._la_libname}.so'
                so = os.path.join(self._package_lib_dir, soname)
                self.run(f'patchelf --set-soname {soname} {so}')

            self.copy("*.dylib", dst="lib", src=self._package_lib_dir)
            self.copy("*.dll", dst="bin", src=self._package_lib_dir)
            self.copy("*.so", dst="lib", src=self._package_lib_dir)
            self.copy("LexFloatClient.lib", dst="lib", src=self._package_lib_dir)
        else:
            self.copy("*.a", dst="lib", src=self._package_lib_dir)

    def package_info(self):
        self.env_info.LEXFLOATCLIENTDIR = self.package_folder
        self.cpp_info.libs = tools.collect_libs(self)

        if self.settings.os == "Linux" and not self.options.shared:
            self.cpp_info.system_libs.extend(["pthread", "ssl3", "nss3", "nspr4"])
        if self.settings.os == "Macos" and not self.options.shared:
            self.cpp_info.frameworks.extend(["CoreFoundation", "SystemConfiguration", "Security"])
        if self.settings.os == "Windows" and self.options.shared:
            self.env_info.path.append(os.path.join(self.package_folder, "bin"))

        self.cpp_info.names["cmake_find_package"] = self._la_libname
        self.cpp_info.names["cmake_find_package_multi"] = self._la_libname
