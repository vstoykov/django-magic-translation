from setuptools import setup, find_packages

install_requires = [
    'django >= 1.2',
]

setup(
    name="django-magic-translation",
    version='0.1.1',
    author="Venelin Stoykov",
    author_email="vkstoykov@gmail.com",
    description="Another application that try to make Django Framework translatable"
                " to different langues easier.",
    long_description=open("README.rst").read(),
    url="https://github.com/vstoykov/django-magic-translation",
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: "
                                            "Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ])
